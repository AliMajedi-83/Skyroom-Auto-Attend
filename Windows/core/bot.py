import os
import time
import subprocess
import threading
import json
import ctypes
import numpy as np
import pyaudiowpatch as pya
import wave
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from logger import app_logger  # استفاده از لاگر جدید اضافه شده به پروژه

def get_screen_resolution():
    try:
        user32 = ctypes.windll.user32
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        return f"{width}x{height}"
    except Exception:
        return "1920x1080"

class SkyroomClassBot:
    def __init__(self, class_data):
        self.class_data = class_data
        self.is_running = True
        self.driver = None
        self.ffmpeg_process = None
        
        self.id, self.user_name, self.password, self.class_name, self.link, \
        self.schedule_json, self.rec_video, self.rec_audio, self.save_path, self.silence_timeout = self.class_data
        
        # استخراج تنظیمات پیشرفته (Pause, Max Duration)
        try:
            sched = json.loads(self.schedule_json)
            settings = sched.get("_settings", {})
            self.pause_sec = int(settings.get("pause_sec", 60))
            self.max_dur_min = int(settings.get("max_dur", 90))
        except:
            self.pause_sec = 60
            self.max_dur_min = 90
            
        timestamp = time.strftime("%Y%m%d_%H%M")
        self.base_filename = os.path.join(self.save_path, f"{self.class_name}_{timestamp}")
        
        # متغیرهای مربوط به مدیریت فایل‌های موقت (مانند نسخه قبلی ویندوز)
        self.video_temp = f"{self.base_filename}_temp.mp4"
        self.audio_temp = f"{self.base_filename}_temp.wav"
        
        self.ffmpeg_path = os.path.join("bin", "ffmpeg.exe") if os.path.exists(os.path.join("bin", "ffmpeg.exe")) else "ffmpeg"
        
        # متغیرهای وضعیت Pause
        self.is_paused = True # کلاس در ابتدا متوقف است تا اولین صدا شنیده شود
        self.class_start_time = None
        self.recorded_video_parts = []
        self.recorded_audio_parts = []
        self.part_num = 0
        self.last_reload_time = 0
        self.needs_reload = False

    def start(self):
        app_logger.info(f"Starting class session: {self.class_name}. Waiting for the first sound to begin recording...")
        self.class_start_time = time.time()
        
        # اجرای مرورگر
        threading.Thread(target=self.run_browser).start()
        
        time.sleep(15)
        # اجرای همزمان ضبط و مانیتورینگ صدا
        threading.Thread(target=self.capture_and_monitor).start()

    def start_recording_part(self):
        # این تابع زمانی فراخوانی می‌شود که صدا شنیده شود
        try:
            current_video = f"{self.video_temp}_part{self.part_num:03d}.mp4"
            current_audio = f"{self.audio_temp}_part{self.part_num:03d}.wav"
            
            if self.rec_video:
                self.recorded_video_parts.append(current_video)
                resolution = get_screen_resolution()
                app_logger.info(f"Recording Windows screen [Part {self.part_num}] started (Video Only).")
                cmd = [
                    self.ffmpeg_path, "-y", "-f", "gdigrab", "-framerate", "15", "-video_size", resolution, "-i", "desktop",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "34", current_video
                ]

                self.ffmpeg_process = subprocess.Popen(
                    cmd, 
                    stdin=subprocess.PIPE, 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
               
            if self.rec_audio or self.rec_video:
                 self.recorded_audio_parts.append(current_audio)
                 # فایل wav در خود تابع capture_and_monitor مدیریت می‌شود، اینجا فقط مسیر را تعیین کردیم.
                 
        except Exception as e:
            app_logger.error(f"Failed to start FFmpeg recording: {e}")

    def pause_recording(self):
        # متوقف کردن ضبط تصویر
        if self.ffmpeg_process:
            try:
                 self.ffmpeg_process.communicate(b'q', timeout=5)
            except subprocess.TimeoutExpired:
                 self.ffmpeg_process.terminate()
                 self.ffmpeg_process.wait()
            self.ffmpeg_process = None
            
        self.is_paused = True
        app_logger.info(f"Recording PAUSED (Silence > {self.pause_sec}s). Saving disk space.")

    def resume_recording(self):
        self.part_num += 1
        self.is_paused = False
        app_logger.info("Sound detected! RESUMING recording in a new part.")
        self.start_recording_part()

    def capture_and_monitor(self):
        # منطق اصلی ضبط صدا با pyaudiowpatch دقیقا مطابق خواسته شما حفظ شد
        if not (self.rec_audio or self.rec_video):
            return

        p = pya.PyAudio()
        try:
            wasapi_info = p.get_host_api_info_by_type(pya.paWASAPI)
            default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
            target_device = None
            if not default_speakers["isLoopbackDevice"]:
                for loopback in p.get_loopback_device_info_generator():
                    if default_speakers["name"] in loopback["name"]:
                        target_device = loopback
                        break
                if not target_device:
                    target_device = p.get_default_wasapi_loopback()
            else:
                target_device = default_speakers

            device_index = target_device["index"]
            channels = int(target_device["maxInputChannels"])
            samplerate = int(target_device["defaultSampleRate"])

            app_logger.info(f"Perfect Audio Capture Engine Initialized: {target_device['name']}")

            silence_start = time.time()
            threshold = 300  # حد آستانه سکوت
            
            wf = None # فایل wav کنونی
            
            stream = p.open(
                format=pya.paInt16,
                channels=channels,
                rate=samplerate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=4096
            )

            while self.is_running:
                try:
                    # بررسی حداکثر زمان کلاس
                    if self.class_start_time and (time.time() - self.class_start_time) >= (self.max_dur_min * 60):
                        app_logger.info(f"Max class duration reached ({self.max_dur_min} mins). Forcing termination.")
                        self.stop_all()
                        break

                    data = stream.read(4096, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    volume = np.max(np.abs(audio_data)) if len(audio_data) > 0 else 0
                    
                    bar_length = min(int(volume / 500), 50)
                    bars = "█" * bar_length

                    if volume < threshold:
                        if silence_start is None:
                            silence_start = time.time()
                        else:
                            elapsed = time.time() - silence_start
                            
                            # Pause کردن ضبط پس از pause_sec ثانیه سکوت
                            if not self.is_paused and elapsed >= self.pause_sec:
                                self.pause_recording()
                                if wf:
                                    wf.close()
                                    wf = None


                            if elapsed >= 30:
                                if time.time() - getattr(self, 'last_reload_time', 0) >= 20:
                                    self.needs_reload = True
                                    self.last_reload_time = time.time()

                                    
                            # خروج کامل پس از silence_timeout دقیقه
                            if elapsed >= (self.silence_timeout * 60):
                                print(f"\n[ALERT] {self.silence_timeout} minutes of pure silence reached! Exiting...")
                                app_logger.info("Total silence exit threshold reached.")
                                self.stop_all()
                                break
                                
                            if elapsed >= 10 and not self.is_paused:
                                print(f"\r[Silence Timer: {elapsed:.1f}s] {bars}".ljust(75), end="", flush=True)
                    else:
                        if silence_start is not None:
                            if self.is_paused:
                                self.resume_recording()
                                # باز کردن فایل wav جدید برای این پارت
                                current_audio = self.recorded_audio_parts[-1]
                                wf = wave.open(current_audio, 'wb')
                                wf.setnchannels(channels)
                                wf.setsampwidth(p.get_sample_size(pya.paInt16))
                                wf.setframerate(samplerate)
                            elif (time.time() - silence_start) >= 10:
                                print("\n[INFO] Sound detected! Silence timer reset.")
                        silence_start = None
                        
                        if not self.is_paused:
                            print(f"\r[Class Audio: {volume}] {bars}".ljust(75), end="", flush=True)
                            
                    # نوشتن دیتا در فایل wav اگر ضبط در حال انجام است
                    if not self.is_paused and wf:
                         wf.writeframes(data)

                except Exception as read_exc:
                    time.sleep(0.1)

            stream.stop_stream()
            stream.close()
            if wf:
                 wf.close()

        except Exception as e:
            app_logger.error(f"Unified capture failed: {e}")
        finally:
            p.terminate()

    def merge_recorded_parts(self):
        # ترکیب پارت‌های ضبط شده تصویر
        final_video = None
        if self.rec_video and self.recorded_video_parts:
            if len(self.recorded_video_parts) == 1:
                final_video = self.video_temp
                if os.path.exists(self.recorded_video_parts[0]):
                    os.rename(self.recorded_video_parts[0], final_video)
            else:
                app_logger.info(f"Merging {len(self.recorded_video_parts)} video parts...")
                concat_file = f"{self.base_filename}_vconcat.txt"
                final_video = self.video_temp
                try:
                    with open(concat_file, "w") as f:
                        for part in self.recorded_video_parts:
                            if os.path.exists(part):
                                f.write(f"file '{os.path.basename(part)}'\n")
                                
                    merge_cmd = [self.ffmpeg_path, "-y", "-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", final_video]
                    subprocess.run(
                        merge_cmd, 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )

                    os.remove(concat_file)
                    for part in self.recorded_video_parts:
                        if os.path.exists(part): os.remove(part)
                except Exception as e:
                    app_logger.error(f"Failed to merge video parts: {e}")
                    
        # ترکیب پارت‌های ضبط شده صدا
        final_audio = None
        if (self.rec_video or self.rec_audio) and self.recorded_audio_parts:
             if len(self.recorded_audio_parts) == 1:
                  final_audio = self.audio_temp
                  if os.path.exists(self.recorded_audio_parts[0]):
                       os.rename(self.recorded_audio_parts[0], final_audio)
             else:
                  app_logger.info(f"Merging {len(self.recorded_audio_parts)} audio parts...")
                  # ترکیب wav فایل‌ها
                  final_audio = self.audio_temp
                  try:
                      out_wav = wave.open(final_audio, 'wb')
                      in_wav_params = None
                      for part in self.recorded_audio_parts:
                           if os.path.exists(part):
                                in_wav = wave.open(part, 'rb')
                                if not in_wav_params:
                                     in_wav_params = in_wav.getparams()
                                     out_wav.setparams(in_wav_params)
                                out_wav.writeframes(in_wav.readframes(in_wav.getnframes()))
                                in_wav.close()
                                os.remove(part)
                      out_wav.close()
                  except Exception as e:
                      app_logger.error(f"Failed to merge audio parts: {e}")
                      
        return final_video, final_audio

    def stop_all(self):
        if not self.is_running: return
        self.is_running = False
        
        if self.ffmpeg_process:
            app_logger.info("Saving video file. Please wait...")
            try:
                self.ffmpeg_process.communicate(b'q', timeout=15)
            except subprocess.TimeoutExpired:
                self.ffmpeg_process.terminate()
                self.ffmpeg_process.wait()
            self.ffmpeg_process = None
            
        final_vid_temp, final_aud_temp = self.merge_recorded_parts()
            
        if self.rec_video and self.rec_audio and final_vid_temp and final_aud_temp:
            app_logger.info("Merging perfect audio and video into final MP4... Please wait!")
            final_mp4 = f"{self.base_filename}.mp4"
            cmd = [
                self.ffmpeg_path, "-y", 
                "-i", final_vid_temp, 
                "-i", final_aud_temp, 
                "-c:v", "copy", "-c:a", "aac", "-b:a", "32k", final_mp4 # کاهش بیت ریت صدا مشابه لینوکس
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            app_logger.info(f"Final class recording saved: {final_mp4}")
            
            try:
                os.remove(final_vid_temp)
                os.remove(final_aud_temp)
            except: pass
            
            # استخراج MP3 نهایی
            app_logger.info("Extracting MP3 from the final MP4...")
            mp3_file = f"{self.base_filename}.mp3"
            extract_cmd = [self.ffmpeg_path, "-y", "-i", final_mp4, "-c:a", "libmp3lame", "-ab", "32k", "-ac", "1", "-ar", "44100", "-vn", mp3_file]
            subprocess.run(extract_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            app_logger.info("Audio extraction completed.")
            
        elif self.rec_video and final_vid_temp:
             os.rename(final_vid_temp, f"{self.base_filename}.mp4")
             app_logger.info(f"Final video saved: {self.base_filename}.mp4")
             
        elif self.rec_audio and final_aud_temp:
            app_logger.info("Converting WAV to final MP3...")
            final_mp3 = f"{self.base_filename}.mp3"
            cmd = [
                self.ffmpeg_path, "-y", "-i", final_aud_temp, "-c:a", "libmp3lame", "-ab", "32k", "-ac", "1", "-ar", "44100", final_mp3
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
            app_logger.info(f"Final audio saved: {final_mp3}")
            
            try:
                os.remove(final_aud_temp)
            except: pass

    def perform_login(self):
        try:
            wait = WebDriverWait(self.driver, 20)
            if self.user_name and self.password:
                user_input = wait.until(EC.presence_of_element_located((By.ID, "username")))
                user_input.clear()
                user_input.send_keys(self.user_name)
                
                pass_input = self.driver.find_element(By.ID, "password")
                pass_input.clear()
                pass_input.send_keys(self.password)
                
                self.driver.find_element(By.ID, "btn_login").click()
                app_logger.info("Logged in with credentials.")
            else:
                wait.until(EC.element_to_be_clickable((By.ID, "btn_guest"))).click()
                app_logger.info("Logged in as guest.")
        except Exception as e:
            app_logger.error(f"Login timeout or error: {e}")


    def run_browser(self):
        app_logger.info("Launching browser: CHROME")
        
        try:
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            chrome_options = ChromeOptions()

            chrome_options.add_argument("--disable-notifications")
            
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            driver_path = os.path.join("bin", "chromedriver.exe")
            if os.path.exists(driver_path):
                from selenium.webdriver.chrome.service import Service as ChromeService
                service = ChromeService(executable_path=driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
                
            self.driver.maximize_window()
            app_logger.info("Browser maximized.")
            
            self.driver.get(self.link)
            wait = WebDriverWait(self.driver, 20)
            
            self.driver.get(self.link)
            
            # --- ورود اولیه به کلاس ---
            self.perform_login()
            
            while self.is_running:
                try:
                    _ = self.driver.window_handles
                    
                    # --- منطق بارگذاری مجدد و ورود دوباره (re-login) ---
                    if getattr(self, 'needs_reload', False):
                        app_logger.info("Silence > 30s. Auto-reloading and re-joining Skyroom...")
                        self.driver.get(self.link)  # باز کردن مجدد لینک
                        time.sleep(3) # مکث کوتاه برای لود شدن فرم
                        self.perform_login() # لاگین مجدد
                        self.needs_reload = False
                        
                except Exception:
                    app_logger.info("Browser window was closed manually. Saving recordings...")
                    self.stop_all()
                    break
                
                time.sleep(1) # کاهش زمان اسلیپ به ۱ ثانیه برای واکنش سریع‌تر
                
        except Exception as e:
            app_logger.error(f"Browser error: {e}")
            self.stop_all()
        finally:
            if self.driver:
                try: self.driver.quit()
                except: pass

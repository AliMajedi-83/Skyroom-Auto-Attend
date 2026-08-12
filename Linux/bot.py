import os
import time
import subprocess
import threading
import json
import numpy as np
import sounddevice as sd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from logger import app_logger


def set_internal_audio_as_default():
    try:
        output = subprocess.check_output("pactl list short sources | grep monitor", shell=True, text=True)
        monitor_name = output.split('\n')[0].split('\t')[1]
        subprocess.run(["pactl", "set-default-source", monitor_name], check=True)
        os.environ["PULSE_SOURCE"] = monitor_name
        app_logger.info(f"Audio successfully forced to internal monitor: {monitor_name}")
        return True
    except Exception as e:
        app_logger.error(f"Failed to set pulse source: {e}")
        return False


def get_screen_resolution():
    try:
        output = subprocess.check_output("xrandr | grep '\\*'", shell=True, text=True)
        return output.split()[0]
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
        
        self.part_num = 0 
        self.recorded_parts = []
        self.is_paused = True 
        self.class_start_time = None
        self.class_start_time = None
        self.last_reload_time = 0
        self.needs_reload = False


    def start(self):
        app_logger.info(f"Starting class session: {self.class_name}. Waiting for the first sound to begin recording...")
        self.class_start_time = time.time()
        threading.Thread(target=self.run_browser).start()
        
        time.sleep(15)
        set_internal_audio_as_default()
        

        threading.Thread(target=self.monitor_silence).start()

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
                app_logger.info("Successfully logged in as a registered user.")
                

            elif self.user_name and not self.password:

                wait.until(EC.element_to_be_clickable((By.ID, "btn_guest"))).click()
                


                guest_name_input = wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".dialog-content input.full-width")
                ))
                guest_name_input.clear()
                guest_name_input.send_keys(self.user_name)
                

                submit_guest_btn = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, ".dialog-footer button.btn")
                ))
                submit_guest_btn.click()
                
                app_logger.info(f"Successfully logged in as GUEST with name: {self.user_name}")
                
            else:
                app_logger.error("Username is required but was not provided. Cannot join class.")

                self.stop_all()

        except Exception as e:
            app_logger.error(f"Login timeout or error: {e}")




    def run_browser(self):
        app_logger.info("Launching browser: FIREFOX")
        try:
            firefox_options = FirefoxOptions()
            driver_path = "./geckodriver"
            if os.path.exists(driver_path):
                service = FirefoxService(executable_path=driver_path)
                self.driver = webdriver.Firefox(service=service, options=firefox_options)
            else:
                self.driver = webdriver.Firefox(options=firefox_options)
            
            self.driver.maximize_window()
            self.driver.get(self.link)
            
            self.perform_login()
            
            while self.is_running:
                try:
                    _ = self.driver.window_handles
                    
                    if getattr(self, 'needs_reload', False):
                        app_logger.info("Silence > 30s. Auto-reloading and re-joining Skyroom...")
                        self.driver.get(self.link)  # باز کردن مجدد لینک مطمئن‌تر از رفرش است
                        time.sleep(3) # مکث کوتاه برای لود شدن فرم‌های اسکای روم
                        self.perform_login() # لاگین مجدد
                        self.needs_reload = False
                        
                except Exception:
                    app_logger.info("Browser window was closed manually. Saving recordings...")
                    self.stop_all()
                    break
                
                time.sleep(1)
                
        except Exception as e:
            app_logger.error(f"Browser execution error: {e}")
            self.stop_all()
        finally:
            if self.driver:
                try: self.driver.quit()
                except: pass



    def start_recording(self):
        try:
            ext = "mp4" if self.rec_video else "mp3"
            output_file = f"{self.base_filename}_part{self.part_num:03d}.{ext}"
            self.recorded_parts.append(output_file)
            
            if self.rec_video:
                resolution = get_screen_resolution()
                app_logger.info(f"Recording video [Part {self.part_num}] started.")
                cmd = [
                    "ffmpeg", "-y", "-video_size", resolution, "-framerate", "15", 
                    "-f", "x11grab", "-i", ":0.0", "-f", "pulse", "-i", "default",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "34", 
                    "-c:a", "aac", "-b:a", "32k", "-ac", "1", "-ar", "44100", output_file
                ]
            elif self.rec_audio:
                app_logger.info(f"Recording audio [Part {self.part_num}] started.")
                cmd = [
                    "ffmpeg", "-y", "-f", "pulse", "-i", "default",
                    "-c:a", "libmp3lame", "-ab", "32k", "-ac", "1", "-ar", "44100", output_file
                ]
            else:
                return
                
            self.ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            app_logger.error(f"Failed to start FFmpeg recording: {e}")

    def pause_recording(self):
        if self.ffmpeg_process:
            self.ffmpeg_process.terminate()
            self.ffmpeg_process.wait()
            self.ffmpeg_process = None
        self.is_paused = True
        app_logger.info(f"Recording PAUSED (Silence > {self.pause_sec}s). Saving disk space.")

    def resume_recording(self):
        self.part_num += 1
        self.is_paused = False
        app_logger.info("Sound detected! RESUMING recording in a new part.")
        self.start_recording()

    def monitor_silence(self):
        silence_start = time.time()
        threshold = 0.01 
        
        def audio_callback(indata, frames, time_info, status):
            nonlocal silence_start
            volume = np.sqrt(np.mean(indata**2))
            
            bar_length = min(int(volume * 150), 50)
            bars = "█" * bar_length
            
            if self.class_start_time and (time.time() - self.class_start_time) >= (self.max_dur_min * 60):
                app_logger.info(f"Max class duration reached ({self.max_dur_min} mins). Forcing termination.")
                self.stop_all()
                raise sd.CallbackStop()

            if volume < threshold:
                if silence_start is None:
                    silence_start = time.time()
                else:
                    elapsed = time.time() - silence_start
                    
                    if not self.is_paused and elapsed >= self.pause_sec:
                        self.pause_recording()

                    if elapsed >= 30:
                        if time.time() - getattr(self, 'last_reload_time', 0) >= 20:
                            self.needs_reload = True
                            self.last_reload_time = time.time()
                    
                    if elapsed >= (self.silence_timeout * 60):
                        print(f"\n[ALERT] {self.silence_timeout} minutes of pure silence reached! Exiting...")
                        app_logger.info("Total silence exit threshold reached.")
                        self.stop_all()
                        raise sd.CallbackStop()
                        
                    if elapsed >= 10 and not self.is_paused:
                        print(f"\r[Silence Timer: {elapsed:.1f}s] {bars}".ljust(75), end="", flush=True)
            else:
                if silence_start is not None:
                    if self.is_paused:
                        self.resume_recording()
                    elif (time.time() - silence_start) >= 10:
                        print("\n[INFO] Sound detected! Silence timer reset.")
                silence_start = None
                
                if not self.is_paused:
                    print(f"\r[Class Audio: {volume:.5f}] {bars}".ljust(75), end="", flush=True)

        try:
            with sd.InputStream(device="pulse", callback=audio_callback, channels=1, samplerate=44100):
                while self.is_running:
                    time.sleep(1)
        except sd.CallbackStop:
            pass
        except Exception as e:
            app_logger.error(f"Sound monitor crashed: {e}")

    def merge_recorded_parts(self):
        if not self.recorded_parts:
            app_logger.info("No audio was recorded during this session (Class was empty).")
            return None
            
        ext = "mp4" if self.rec_video else "mp3"
        final_file = f"{self.base_filename}.{ext}"
        
        if len(self.recorded_parts) == 1:
            os.rename(self.recorded_parts[0], final_file)
            return final_file
            
        app_logger.info(f"Merging {len(self.recorded_parts)} recorded parts into one file...")
        concat_file = f"{self.base_filename}_concat.txt"
        
        try:
            with open(concat_file, "w") as f:
                for part in self.recorded_parts:
                    if os.path.exists(part):
                        f.write(f"file '{part}'\n")
                        
            merge_cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", final_file]
            subprocess.run(merge_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            os.remove(concat_file)
            for part in self.recorded_parts:
                if os.path.exists(part): os.remove(part)
                
            app_logger.info("Merge completed successfully.")
            return final_file
        except Exception as e:
            app_logger.error(f"Failed to merge parts: {e}")
            return None
    def stop_all(self):
        if not self.is_running: return 
        self.is_running = False
        
        if self.ffmpeg_process:
            self.ffmpeg_process.terminate()
            self.ffmpeg_process.wait()
            self.ffmpeg_process = None
            
        threading.Thread(target=self._process_media_files, daemon=False).start()

    def _process_media_files(self):
        final_media = self.merge_recorded_parts()
            
        if self.rec_video and self.rec_audio and final_media:
            app_logger.info("Extracting MP3 from the final MP4...")
            mp3_file = f"{self.base_filename}.mp3"
            extract_cmd = ["ffmpeg", "-y", "-i", final_media, "-c:a", "libmp3lame", "-ab", "32k", "-ac", "1", "-ar", "44100", "-vn", mp3_file]
            subprocess.run(extract_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            app_logger.info("Audio extraction completed.")

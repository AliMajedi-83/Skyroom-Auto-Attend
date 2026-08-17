import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import database
import time
import threading
import json
import os
import datetime
from bot import SkyroomClassBot
from logger import app_logger

class SkyroomGUI:
    def __init__(self, root):

        self.root = root
        self.root.title("Skyroom Auto-Attend Bot (Windows Edition)")
        self.root.geometry("950x800")

        self.active_bots = []
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing) 
        
        app_logger.info("Initializing Skyroom GUI application (Windows Edition).")
        database.init_db()
        self.editing_id = None
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.tab_list = ttk.Frame(self.notebook)
        self.tab_add = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_list, text="Class List")
        self.notebook.add(self.tab_add, text="Add / Edit Class")
        
        self.build_list_tab()
        self.build_add_tab()
        
        threading.Thread(target=self.scheduler_thread, daemon=True).start()



    def on_closing(self):
        running_bots = [bot for bot in self.active_bots if bot.is_running]
        
        if running_bots:
            msg = "A class session is currently active.\nIf you exit, Chrome will close and the video will be saved in the background terminal.\n\nAre you sure you want to exit?"
            if not messagebox.askyesno("Confirm Exit", msg):
                return
                
        app_logger.info("GUI closed by user. Safely saving all files in the background...")
        
        self.root.withdraw()
        
        def background_save():
            for bot in self.active_bots:
                if bot.is_running:
                    bot.stop_all()
                    
            for bot in self.active_bots:
                if hasattr(bot, 'browser_thread') and bot.browser_thread.is_alive():
                    bot.browser_thread.join()
                if hasattr(bot, 'capture_thread') and bot.capture_thread.is_alive():
                    bot.capture_thread.join()
                    
            app_logger.info("All background tasks finished. Exiting program gracefully.")
            os._exit(0)  
            
        save_thread = threading.Thread(target=background_save)
        save_thread.start()

    def build_list_tab(self):
        columns = ("db_id", "row_num", "user", "class", "schedule", "mode")
        self.tree = ttk.Treeview(self.tab_list, columns=columns, show="headings", 
                                 displaycolumns=("row_num", "user", "class", "schedule", "mode"))
        
        self.tree.heading("row_num", text="#")
        self.tree.heading("user", text="User")
        self.tree.heading("class", text="Class Name")
        self.tree.heading("schedule", text="Schedule")
        self.tree.heading("mode", text="Recording Mode")
        
        self.tree.column("row_num", width=40, stretch=False, anchor=tk.CENTER)
        self.tree.column("user", width=100)
        self.tree.column("class", width=180)
        self.tree.column("schedule", width=330)
        self.tree.column("mode", width=150, anchor=tk.CENTER)
        
        self.tree.pack(fill=tk.BOTH, expand=True, pady=10)
        
        btn_frame = tk.Frame(self.tab_list)
        btn_frame.pack(fill=tk.X)
        
        tk.Button(btn_frame, text="▶ Join Class Now", bg="#ff9800", fg="black", font=("Arial", 9, "bold"), command=self.join_now).pack(side=tk.LEFT, padx=5)
        
        self.btn_ignore = tk.Button(btn_frame, text="⏸ Ignore Next Session", bg="#607d8b", fg="white", font=("Arial", 9, "bold"), command=self.toggle_ignore_next)
        self.btn_ignore.pack(side=tk.LEFT, padx=5)
        self.btn_ignore.config(state=tk.DISABLED) 
        
        tk.Button(btn_frame, text="Delete Class", bg="#ff4c4c", fg="white", command=self.delete_selected).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Edit Class", bg="#2196F3", fg="white", command=self.edit_selected).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Refresh List", command=self.refresh_list).pack(side=tk.RIGHT, padx=5)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.refresh_list()

    def build_add_tab(self):
        form = tk.Frame(self.tab_add)
        form.pack(pady=20, padx=20, fill=tk.BOTH)
        
        tk.Label(form, text="User Name / Guest Name (Required):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.ent_user = tk.Entry(form)
        self.ent_user.grid(row=0, column=1, pady=5, sticky=tk.EW)
        
        tk.Label(form, text="Password (Optional):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.ent_pass = tk.Entry(form, show="*")
        self.ent_pass.grid(row=1, column=1, pady=5, sticky=tk.EW)
        
        help_lbl = tk.Label(form, text="* Note: Leave Password blank to join as GUEST.", fg="gray", font=("Arial", 9, "italic"))
        help_lbl.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))
        
        tk.Label(form, text="Class Name (Required):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.ent_class = tk.Entry(form)
        self.ent_class.grid(row=3, column=1, pady=5, sticky=tk.EW)
        
        tk.Label(form, text="Class Link (Required):").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.ent_link = tk.Entry(form)
        self.ent_link.grid(row=4, column=1, pady=5, sticky=tk.EW)
        
        tk.Label(form, text="Schedule:").grid(row=5, column=0, sticky=tk.NW, pady=5)
        days_frame = tk.Frame(form)
        days_frame.grid(row=5, column=1, sticky=tk.W, pady=5)
        
        self.days_data = {}
        days_list = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        
        for day in days_list:
            row_frame = tk.Frame(days_frame)
            row_frame.pack(fill=tk.X, pady=2)
            var = tk.BooleanVar()
            chk = tk.Checkbutton(row_frame, text=day, variable=var, width=12, anchor=tk.W)
            chk.pack(side=tk.LEFT)
            ent_time = tk.Entry(row_frame, width=10)
            ent_time.insert(0, "08:00")
            ent_time.pack(side=tk.LEFT, padx=5)
            self.days_data[day] = (var, ent_time)
            
        tk.Label(form, text="Recording Options:").grid(row=6, column=0, sticky=tk.W, pady=10)
        mode_frame = tk.Frame(form)
        mode_frame.grid(row=6, column=1, sticky=tk.W, pady=10)
        self.var_video = tk.BooleanVar(value=True)
        self.var_audio = tk.BooleanVar(value=True)
        tk.Checkbutton(mode_frame, text="Record Video", variable=self.var_video, command=self.toggle_recording_settings).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(mode_frame, text="Record Audio", variable=self.var_audio, command=self.toggle_recording_settings).pack(side=tk.LEFT, padx=5)
        
        tk.Label(form, text="Pause record if silence (sec):").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.ent_pause = tk.Entry(form)
        self.ent_pause.insert(0, "60")
        self.ent_pause.grid(row=7, column=1, pady=5, sticky=tk.EW)
        
        tk.Label(form, text="Exit completely if silence (mins):").grid(row=8, column=0, sticky=tk.W, pady=5)
        self.ent_silence = tk.Entry(form)
        self.ent_silence.insert(0, "15") 
        self.ent_silence.grid(row=8, column=1, pady=5, sticky=tk.EW)
        
        tk.Label(form, text="Max Class Duration (mins):").grid(row=9, column=0, sticky=tk.W, pady=5)
        self.ent_max_dur = tk.Entry(form)
        self.ent_max_dur.insert(0, "90")
        self.ent_max_dur.grid(row=9, column=1, pady=5, sticky=tk.EW)
        
        tk.Label(form, text="Save Path:").grid(row=10, column=0, sticky=tk.W, pady=5)
        self.save_path = tk.StringVar()
        self.save_path.set(os.getcwd())
        path_frame = tk.Frame(form)
        path_frame.grid(row=10, column=1, sticky=tk.EW)
        tk.Button(path_frame, text="Choose Dir", command=self.choose_dir).pack(side=tk.LEFT)
        tk.Label(path_frame, textvariable=self.save_path, fg="blue").pack(side=tk.LEFT, padx=10)
        
        self.btn_save = tk.Button(form, text="Save Class", bg="#4caf50", fg="white", command=self.save_class)
        self.btn_save.grid(row=11, columnspan=2, pady=20)
        form.columnconfigure(1, weight=1)


    def toggle_recording_settings(self):

        if not self.var_video.get() and not self.var_audio.get():
            target_state = tk.DISABLED
        else:
            target_state = tk.NORMAL
            
        self.ent_pause.config(state=target_state)
        self.ent_silence.config(state=target_state)
        self.ent_max_dur.config(state=target_state)


    def choose_dir(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.save_path.set(dir_path)

    def save_class(self):

        user_name_val = self.ent_user.get().strip()
        if not user_name_val:
            messagebox.showerror("Error", "User Name (or Guest Name) is required!")
            return

        class_name_val = self.ent_class.get().strip()
        if not class_name_val:
            messagebox.showerror("Error", "Class Name is required!")
            return
            

        class_link_val = self.ent_link.get().strip()
        if not class_link_val:
            messagebox.showerror("Error", "Class Link is required!")
            return

        schedule_dict = {}
        for day, (var, ent) in self.days_data.items():
            if var.get():
                schedule_dict[day] = ent.get().strip()
                
        if not schedule_dict:
            messagebox.showerror("Error", "Please select at least one day and time!")
            return
            
        schedule_dict["_settings"] = {
            "pause_sec": self.ent_pause.get() or "60",
            "max_dur": self.ent_max_dur.get() or "90",
            "ignore_next": False
        }
        
        schedule_json = json.dumps(schedule_dict)
        
        data = (
            self.ent_user.get(),
            self.ent_pass.get(),
            self.ent_class.get(),
            self.ent_link.get(),
            schedule_json,
            int(self.var_video.get()),
            int(self.var_audio.get()),
            self.save_path.get(),
            int(self.ent_silence.get() or 15)
        )
        
        if self.editing_id:
            database.update_class(self.editing_id, data)
            app_logger.info(f"Class updated successfully: {self.ent_class.get()}")
            messagebox.showinfo("Success", "Class updated successfully!")
            self.editing_id = None
            self.btn_save.config(text="Save Class")
        else:
            database.add_class(data)
            app_logger.info(f"New class added to database: {self.ent_class.get()}")
            messagebox.showinfo("Success", "Class saved successfully!")
            
        self.ent_user.delete(0, tk.END)
        self.ent_pass.delete(0, tk.END)
        self.ent_class.delete(0, tk.END)
        self.ent_link.delete(0, tk.END)
        for var, ent in self.days_data.values():
            var.set(False)
            ent.delete(0, tk.END)
            ent.insert(0, "08:00")
            
        self.refresh_list()
        self.notebook.select(self.tab_list)

    def edit_selected(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Warning", "Please select a class to edit.")
            return
            
        item_id = self.tree.item(selected)['values'][0]
        classes = database.get_classes()
        target = next((c for c in classes if c[0] == item_id), None)
        if not target: return
        
        self.editing_id = item_id
        self.ent_user.delete(0, tk.END); self.ent_user.insert(0, target[1] or "")
        self.ent_pass.delete(0, tk.END); self.ent_pass.insert(0, target[2] or "")
        self.ent_class.delete(0, tk.END); self.ent_class.insert(0, target[3])
        self.ent_link.delete(0, tk.END); self.ent_link.insert(0, target[4])
        
        try:
            schedule_dict = json.loads(target[5])
        except:
            schedule_dict = {}
            
        for day, (var, ent) in self.days_data.items():
            if day in schedule_dict and not day.startswith("_"):
                var.set(True)
                ent.delete(0, tk.END)
                ent.insert(0, schedule_dict[day])
            else:
                var.set(False)
                ent.delete(0, tk.END); ent.insert(0, "08:00")
                
        settings = schedule_dict.get("_settings", {})
        self.ent_pause.delete(0, tk.END); self.ent_pause.insert(0, settings.get("pause_sec", "60"))
        self.ent_max_dur.delete(0, tk.END); self.ent_max_dur.insert(0, settings.get("max_dur", "90"))
        
        self.var_video.set(bool(target[6]))
        self.var_audio.set(bool(target[7]))
        self.save_path.set(target[8])
        self.ent_silence.delete(0, tk.END); self.ent_silence.insert(0, str(target[9]))
        
        self.btn_save.config(text="Update Class")
        self.notebook.select(self.tab_add)
        self.toggle_recording_settings() 

    def on_tree_select(self, event=None):
        selected = self.tree.focus()
        if not selected:
            self.btn_ignore.config(state=tk.DISABLED, text="⏸ Ignore Next Session", bg="#607d8b")
            return
            
        self.btn_ignore.config(state=tk.NORMAL)
        item_id = self.tree.item(selected)['values'][0]
        
        classes = database.get_classes()
        target = next((c for c in classes if c[0] == item_id), None)
        if target:
            try:
                settings = json.loads(target[5]).get("_settings", {})
                is_ignored = settings.get("ignore_next", False)
                if is_ignored:
                    self.btn_ignore.config(text="▶ Restore Next Session", bg="#4caf50")
                else:
                    self.btn_ignore.config(text="⏸ Ignore Next Session", bg="#607d8b")
            except:
                self.btn_ignore.config(text="⏸ Ignore Next Session", bg="#607d8b")

    def toggle_ignore_next(self):
        selected = self.tree.focus()
        if not selected: return
        item_id = self.tree.item(selected)['values'][0]
        
        classes = database.get_classes()
        target = next((c for c in classes if c[0] == item_id), None)
        if not target: return
        
        try:
            sched = json.loads(target[5])
        except:
            sched = {}
            
        settings = sched.get("_settings", {})
        current_state = settings.get("ignore_next", False)
        new_state = not current_state  
        
        settings["ignore_next"] = new_state
        sched["_settings"] = settings
        
        data = (target[1], target[2], target[3], target[4], json.dumps(sched), target[6], target[7], target[8], target[9])
        database.update_class(item_id, data)
        
        state_str = "IGNORED" if new_state else "RESTORED"
        app_logger.info(f"Class '{target[3]}' next session is now {state_str}.")
        
        self.refresh_list()
        self.on_tree_select(None) 

    def refresh_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for index, row in enumerate(database.get_classes(), start=1):
            try:
                sd = json.loads(row[5])
                sched_str = ", ".join([f"{k[:3]} {v}" for k, v in sd.items() if not k.startswith("_")])
                
                settings = sd.get("_settings", {})
                display_name = f"🚫 {row[3]} (Skip Next)" if settings.get("ignore_next", False) else row[3]
            except:
                sched_str = "Error reading schedule"
                display_name = row[3]
            
            mode_list = []
            if row[6]: mode_list.append("Video")
            if row[7]: mode_list.append("Audio")
            mode_str = " + ".join(mode_list) if mode_list else "None"
            self.tree.insert("", tk.END, values=(row[0], index, row[1] or "Guest", display_name, sched_str, mode_str))

    def delete_selected(self):
        selected = self.tree.focus()
        if not selected: return
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this class?"):
            item_id = self.tree.item(selected)['values'][0]
            database.delete_class(item_id)
            self.refresh_list()
            self.on_tree_select(None)

    
    def stop_existing_bots(self):
        # این تابع تمام ربات‌های فعال را پیدا کرده و با آرامش می‌بندد
        running_bots = [b for b in self.active_bots if b.is_running]
        if running_bots:
            app_logger.info("Closing previous active classes before starting a new one...")
            for bot in running_bots:
                bot.stop_all()
            self.active_bots.clear()

    def join_now(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Warning", "Please select a class from the list.")
            return
        item_id = self.tree.item(selected)['values'][0]
        classes = database.get_classes()
        target = next((c for c in classes if c[0] == item_id), None)
        if not target: return
        
        if messagebox.askyesno("Join Now", f"Start '{target[3]}' immediately?"):
            app_logger.info(f"Manual join requested for class: {target[3]}")
            
            # اجرای فرآیند توقف و استارت در یک ترد جداگانه تا رابط گرافیکی (GUI) فریز نشود
            def launch_new_bot():
                self.stop_existing_bots()
                bot = SkyroomClassBot(target)
                self.active_bots.append(bot)
                bot.start()
                
            threading.Thread(target=launch_new_bot, daemon=True).start()


    def scheduler_thread(self):
        app_logger.info("Background scheduler thread started successfully.")
        while True:
            now = datetime.datetime.now()
            current_time = now.strftime("%H:%M")
            current_day = now.strftime("%A") 
            
            classes = database.get_classes()
            for cls in classes:
                try:
                    schedule_dict = json.loads(cls[5])
                    if current_day in schedule_dict and schedule_dict[current_day] == current_time:
                        
                        settings = schedule_dict.get("_settings", {})
                        if settings.get("ignore_next", False):
                            app_logger.info(f"Skipping scheduled session for '{cls[3]}' (Ignore Next active). Resetting flag for future sessions.")
                            settings["ignore_next"] = False
                            schedule_dict["_settings"] = settings
                            
                            data = (cls[1], cls[2], cls[3], cls[4], json.dumps(schedule_dict), cls[6], cls[7], cls[8], cls[9])
                            database.update_class(cls[0], data)
                            self.root.after(0, self.refresh_list) 
                            
                            time.sleep(60)
                            continue
                            
                        app_logger.info(f"Schedule matched! Initializing bot for class: {cls[3]}")
                        
                        def scheduled_launch():
                            self.stop_existing_bots()
                            bot = SkyroomClassBot(cls)
                            self.active_bots.append(bot)
                            bot.start()
                            
                        threading.Thread(target=scheduled_launch, daemon=True).start()
                        time.sleep(60) 
                except Exception as e:
                    app_logger.error(f"Error in scheduler loop: {e}", exc_info=True)
            time.sleep(30)


if __name__ == "__main__":
    root = tk.Tk()
    app = SkyroomGUI(root)
    root.mainloop()

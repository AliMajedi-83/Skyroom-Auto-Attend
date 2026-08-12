import argparse
import database
import json
import os
import time
from bot import SkyroomClassBot
from logger import app_logger

DAYS_MAP = {
    "1": "Saturday",
    "2": "Sunday",
    "3": "Monday",
    "4": "Tuesday",
    "5": "Wednesday",
    "6": "Thursday",
    "7": "Friday"
}

def print_banner():
    print("="*60)
    print("🎓 Skyroom Auto-Attend CLI Manager")
    print("="*60)

def list_classes():
    classes = database.get_classes()
    if not classes:
        print("\n📭 No classes found in the database.\n")
        return
        
    print("\n{:<5} | {:<15} | {:<20} | {:<10} | {:<10}".format("ID", "Class Name", "Schedule", "Mode", "Status"))
    print("-" * 75)
    for row in classes:
        try:
            sched = json.loads(row[5])
            sched_str = ", ".join([f"{k[:3]} {v}" for k, v in sched.items() if not k.startswith("_")])
            
            settings = sched.get("_settings", {})
            status = "🚫 Ignored" if settings.get("ignore_next", False) else "✅ Active"
        except:
            sched_str = "Invalid Schedule"
            status = "Unknown"
            
        mode = []
        if row[6]: mode.append("Video")
        if row[7]: mode.append("Audio")
        mode_str = "+".join(mode) if mode else "None"
        
        print("{:<5} | {:<15} | {:<20} | {:<10} | {:<10}".format(row[0], row[3][:15], sched_str[:20], mode_str, status))
    print("-" * 75 + "\n")

def add_class():
    print_banner()
    print("📝 Adding a new class (Leave User/Pass blank for GUEST mode)")
    
    user_name = ""
    while not user_name:
        user_name = input("Username / Guest Name (Required): ").strip()

    password = input("Password (Optional): ").strip()
    
    class_name = ""
    while not class_name:
        class_name = input("Class Name (Required): ").strip()
        
    link = ""
    while not link:
        link = input("Class Link (Required): ").strip()
    
    print("\n📅 Schedule Setup")
    schedule_dict = {}
    
    while True:
        print("Options: [1]Sat [2]Sun [3]Mon [4]Tue [5]Wed [6]Thu [7]Fri")
        day_num = input("Enter day number (1-7) or 'done' to finish: ").strip().lower()
        if day_num == 'done':
            if schedule_dict:
                break
            else:
                print("⚠️ You must add at least one schedule day!")
                continue
                
        if day_num not in DAYS_MAP:
            print("❌ Invalid option. Please enter a number from 1 to 7.")
            continue
            
        day_name = DAYS_MAP[day_num]
        time_str = input(f"Enter time for {day_name} (HH:MM, e.g., 08:00): ").strip()
        schedule_dict[day_name] = time_str
        print(f"✅ Added: {day_name} at {time_str}\n")

    print("⚙️ Recording & Advanced Settings")
    rec_vid = input("Record Video? (Y/n): ").strip().lower() != 'n'
    rec_aud = input("Record Audio? (Y/n): ").strip().lower() != 'n'
    
    save_path = input(f"Save Path [Default: {os.getcwd()}]: ").strip() or os.getcwd()
    pause_sec = input("Pause record if silence (sec) [Default: 60]: ").strip() or "60"
    silence = input("Exit completely if silence (mins) [Default: 15]: ").strip() or "15"
    max_dur = input("Max Class Duration (mins) [Default: 90]: ").strip() or "90"
    
    schedule_dict["_settings"] = {
        "pause_sec": pause_sec,
        "max_dur": max_dur,
        "ignore_next": False
    }

    data = (
        user_name, password, class_name, link, 
        json.dumps(schedule_dict), 
        int(rec_vid), int(rec_aud), 
        save_path, int(silence)
    )
    
    database.add_class(data)
    print(f"\n🎉 Class '{class_name}' added successfully to the database!\n")

def get_input(prompt, default_val):
    val = input(f"{prompt} [{default_val}]: ").strip()
    return val if val else default_val

def edit_class(class_id):
    classes = database.get_classes()
    target = next((c for c in classes if c[0] == class_id), None)
    
    if not target:
        print(f"\n❌ Class ID {class_id} not found.\n")
        return
        
    print_banner()
    print(f"✏️ Editing Class ID {class_id}: {target[3]}")
    print("Press Enter to keep current values.\n")
    
    user_name = get_input("Username / Guest Name (Required)", target[1] or "")
    while not user_name:
         print("❌ Username cannot be empty!")
         user_name = input("Username / Guest Name (Required): ").strip()

    password = get_input("Password (Optional)", target[2] or "")
    class_name = get_input("Class Name", target[3])
    link = get_input("Class Link", target[4])
    
    try:
        sched = json.loads(target[5])
    except:
        sched = {}
        
    print("\n📅 Current Schedule:")
    for d, t in sched.items():
        if not d.startswith("_"):
            print(f"  - {d}: {t}")
            
    change_sched = input("\nDo you want to change the schedule? (y/N): ").strip().lower() == 'y'
    new_sched = {}
    
    if change_sched:
        while True:
            print("Options: [1]Sat [2]Sun [3]Mon [4]Tue [5]Wed [6]Thu [7]Fri")
            day_num = input("Enter day number (1-7) or 'done': ").strip().lower()
            if day_num == 'done':
                if new_sched: break
                else:
                    print("⚠️ Must add at least one day!")
                    continue
            if day_num not in DAYS_MAP:
                print("❌ Invalid option.")
                continue
            day_name = DAYS_MAP[day_num]
            t_str = input(f"Enter time for {day_name} (HH:MM): ").strip()
            new_sched[day_name] = t_str
            print(f"✅ Added: {day_name} at {t_str}\n")
    else:
        new_sched = {k: v for k, v in sched.items() if not k.startswith("_")}
        
    print("\n⚙️ Settings")
    rec_vid = get_input("Record Video? (1=Yes, 0=No)", "1" if target[6] else "0") == "1"
    rec_aud = get_input("Record Audio? (1=Yes, 0=No)", "1" if target[7] else "0") == "1"
    
    settings = sched.get("_settings", {})
    pause_sec = get_input("Pause record if silence (sec)", settings.get("pause_sec", "60"))
    silence = get_input("Exit completely if silence (mins)", str(target[9]))
    max_dur = get_input("Max Class Duration (mins)", settings.get("max_dur", "90"))
    save_path = get_input("Save Path", target[8])
    
    new_sched["_settings"] = {
        "pause_sec": pause_sec,
        "max_dur": max_dur,
        "ignore_next": settings.get("ignore_next", False)
    }
    
    data = (user_name, password, class_name, link, json.dumps(new_sched), int(rec_vid), int(rec_aud), save_path, int(silence))
    database.update_class(class_id, data)
    print(f"\n✅ Class '{class_name}' updated successfully!\n")

def set_ignore_status(class_id, is_ignored):
    classes = database.get_classes()
    target = next((c for c in classes if c[0] == class_id), None)
    
    if not target:
        print(f"\n❌ Class ID {class_id} not found.\n")
        return
        
    try:
        sched = json.loads(target[5])
    except:
        sched = {}
        
    settings = sched.get("_settings", {})
    settings["ignore_next"] = is_ignored
    sched["_settings"] = settings
    
    data = (target[1], target[2], target[3], target[4], json.dumps(sched), target[6], target[7], target[8], target[9])
    database.update_class(class_id, data)
    
    state_str = "IGNORED (Skip Next)" if is_ignored else "RESTORED (Active)"
    print(f"\n✅ Class '{target[3]}' next session is now {state_str}.\n")

def join_class(class_id):
    classes = database.get_classes()
    target = next((c for c in classes if c[0] == class_id), None)
    
    if not target:
        print(f"\n❌ Class ID {class_id} not found.\n")
        return
        
    print_banner()
    print(f"🚀 Manually joining class: {target[3]}")
    print("Press Ctrl+C at any time to gracefully stop the bot and save files.\n")
    
    try:
        bot = SkyroomClassBot(target)
        bot.start()
        while bot.is_running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⏹️ User interrupted. Stopping bot and saving files safely...")
        bot.stop_all()

def delete_class(class_id):
    classes = database.get_classes()
    exists = any(c[0] == class_id for c in classes)
    
    if exists:
        database.delete_class(class_id)
        print(f"\n🗑️ Class ID {class_id} deleted successfully.\n")
    else:
        print(f"\n❌ Class ID {class_id} not found.\n")


def run_cli_scheduler():
    print_banner()
    print("🕒 Starting CLI Background Scheduler...")
    print("Keeping terminal open to monitor schedule. Press Ctrl+C to stop.\n")
    
    active_bots = []
    
    try:
        while True:
            now = time.localtime()
            current_time = time.strftime("%H:%M", now)
            current_day = time.strftime("%A", now)
            
            classes = database.get_classes()
            for cls in classes:
                try:
                    schedule_dict = json.loads(cls[5])
                    if current_day in schedule_dict and schedule_dict[current_day] == current_time:
                        
                        settings = schedule_dict.get("_settings", {})
                        if settings.get("ignore_next", False):
                            app_logger.info(f"Skipping ignored session for class: {cls[3]}")
                            settings["ignore_next"] = False
                            schedule_dict["_settings"] = settings
                            database.update_class(cls[0], (cls[1], cls[2], cls[3], cls[4], json.dumps(schedule_dict), cls[6], cls[7], cls[8], cls[9]))
                            continue 
                        
                        app_logger.info(f"Schedule matched! Initializing bot for class: {cls[3]}")
                        
                        for active_bot in active_bots:
                            if active_bot.is_running:
                                app_logger.info("Terminating previous class session to prevent overlap.")
                                active_bot.stop_all()
                        
                        active_bots.clear() 

                        bot = SkyroomClassBot(cls)
                        active_bots.append(bot)
                        bot.start()
                        time.sleep(60) 
                except Exception as e:
                    app_logger.error(f"Error in scheduler loop: {e}", exc_info=True)
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Scheduler stopped by user. Cleaning up...")
        for bot in active_bots:
            if bot.is_running:
                bot.stop_all()



def main():
    parser = argparse.ArgumentParser(
        description="Skyroom Auto-Attend CLI Manager",
        epilog="Use 'python3 cli.py <command> -h' for more info on a specific command."
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    subparsers.add_parser("add", help="Add a new class interactively")
    subparsers.add_parser("list", help="List all scheduled classes and their status")

    subparsers.add_parser("start-scheduler", help="Run the background scheduler in the terminal (Keeps terminal open)")
    
    join_parser = subparsers.add_parser("join", help="Join a class immediately by its ID")
    join_parser.add_argument("id", type=int, help="The ID of the class to join")
    
    ignore_parser = subparsers.add_parser("ignore", help="Toggle 'Ignore Next Session' for a class")
    ignore_parser.add_argument("id", type=int, help="The ID of the class to ignore/restore")
    restore_parser = subparsers.add_parser("restore", help="Restore an ignored class (Make it Active)")
    restore_parser.add_argument("id", type=int, help="The ID of the class to restore")
    
    edit_parser = subparsers.add_parser("edit", help="Edit an existing class by its ID")
    edit_parser.add_argument("id", type=int, help="The ID of the class to edit")
    
    del_parser = subparsers.add_parser("delete", help="Delete a class by its ID")
    del_parser.add_argument("id", type=int, help="The ID of the class to delete")

    args = parser.parse_args()
    database.init_db()

    if args.command == "add":
        add_class()
    elif args.command == "list":
        list_classes()
    elif args.command == "join":
        join_class(args.id)
    elif args.command == "ignore":
        set_ignore_status(args.id, True)
    elif args.command == "restore":
        set_ignore_status(args.id, False)
    elif args.command == "edit":
        edit_class(args.id)
    elif args.command == "delete":
        delete_class(args.id)
    elif args.command == "start-scheduler":
        run_cli_scheduler()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()import argparse
import database
import json
import os
import time
from bot import SkyroomClassBot
from logger import app_logger

DAYS_MAP = {
    "1": "Saturday",
    "2": "Sunday",
    "3": "Monday",
    "4": "Tuesday",
    "5": "Wednesday",
    "6": "Thursday",
    "7": "Friday"
}

def print_banner():
    print("="*60)
    print("🎓 Skyroom Auto-Attend CLI Manager")
    print("="*60)

def list_classes():
    classes = database.get_classes()
    if not classes:
        print("\n📭 No classes found in the database.\n")
        return
        
    print("\n{:<5} | {:<15} | {:<20} | {:<10} | {:<10}".format("ID", "Class Name", "Schedule", "Mode", "Status"))
    print("-" * 75)
    for row in classes:
        try:
            sched = json.loads(row[5])
            sched_str = ", ".join([f"{k[:3]} {v}" for k, v in sched.items() if not k.startswith("_")])
            
            settings = sched.get("_settings", {})
            status = "🚫 Ignored" if settings.get("ignore_next", False) else "✅ Active"
        except:
            sched_str = "Invalid Schedule"
            status = "Unknown"
            
        mode = []
        if row[6]: mode.append("Video")
        if row[7]: mode.append("Audio")
        mode_str = "+".join(mode) if mode else "None"
        
        print("{:<5} | {:<15} | {:<20} | {:<10} | {:<10}".format(row[0], row[3][:15], sched_str[:20], mode_str, status))
    print("-" * 75 + "\n")

def add_class():
    print_banner()
    print("📝 Adding a new class (Leave User/Pass blank for GUEST mode)")
    
    user_name = input("Username (Optional): ").strip()
    password = input("Password (Optional): ").strip()
    
    class_name = ""
    while not class_name:
        class_name = input("Class Name (Required): ").strip()
        
    link = ""
    while not link:
        link = input("Class Link (Required): ").strip()
    
    print("\n📅 Schedule Setup")
    schedule_dict = {}
    
    while True:
        print("Options: [1]Sat [2]Sun [3]Mon [4]Tue [5]Wed [6]Thu [7]Fri")
        day_num = input("Enter day number (1-7) or 'done' to finish: ").strip().lower()
        if day_num == 'done':
            if schedule_dict:
                break
            else:
                print("⚠️ You must add at least one schedule day!")
                continue
                
        if day_num not in DAYS_MAP:
            print("❌ Invalid option. Please enter a number from 1 to 7.")
            continue
            
        day_name = DAYS_MAP[day_num]
        time_str = input(f"Enter time for {day_name} (HH:MM, e.g., 08:00): ").strip()
        schedule_dict[day_name] = time_str
        print(f"✅ Added: {day_name} at {time_str}\n")

    print("⚙️ Recording & Advanced Settings")
    rec_vid = input("Record Video? (Y/n): ").strip().lower() != 'n'
    rec_aud = input("Record Audio? (Y/n): ").strip().lower() != 'n'
    
    save_path = input(f"Save Path [Default: {os.getcwd()}]: ").strip() or os.getcwd()
    pause_sec = input("Pause record if silence (sec) [Default: 60]: ").strip() or "60"
    silence = input("Exit completely if silence (mins) [Default: 15]: ").strip() or "15"
    max_dur = input("Max Class Duration (mins) [Default: 90]: ").strip() or "90"
    
    schedule_dict["_settings"] = {
        "pause_sec": pause_sec,
        "max_dur": max_dur,
        "ignore_next": False
    }

    data = (
        user_name, password, class_name, link, 
        json.dumps(schedule_dict), 
        int(rec_vid), int(rec_aud), 
        save_path, int(silence)
    )
    
    database.add_class(data)
    print(f"\n🎉 Class '{class_name}' added successfully to the database!\n")

def get_input(prompt, default_val):
    val = input(f"{prompt} [{default_val}]: ").strip()
    return val if val else default_val

def edit_class(class_id):
    classes = database.get_classes()
    target = next((c for c in classes if c[0] == class_id), None)
    
    if not target:
        print(f"\n❌ Class ID {class_id} not found.\n")
        return
        
    print_banner()
    print(f"✏️ Editing Class ID {class_id}: {target[3]}")
    print("Press Enter to keep current values.\n")
    
    user_name = get_input("Username", target[1] or "")
    password = get_input("Password", target[2] or "")
    class_name = get_input("Class Name", target[3])
    link = get_input("Class Link", target[4])
    
    try:
        sched = json.loads(target[5])
    except:
        sched = {}
        
    print("\n📅 Current Schedule:")
    for d, t in sched.items():
        if not d.startswith("_"):
            print(f"  - {d}: {t}")
            
    change_sched = input("\nDo you want to change the schedule? (y/N): ").strip().lower() == 'y'
    new_sched = {}
    
    if change_sched:
        while True:
            print("Options: [1]Sat [2]Sun [3]Mon [4]Tue [5]Wed [6]Thu [7]Fri")
            day_num = input("Enter day number (1-7) or 'done': ").strip().lower()
            if day_num == 'done':
                if new_sched: break
                else:
                    print("⚠️ Must add at least one day!")
                    continue
            if day_num not in DAYS_MAP:
                print("❌ Invalid option.")
                continue
            day_name = DAYS_MAP[day_num]
            t_str = input(f"Enter time for {day_name} (HH:MM): ").strip()
            new_sched[day_name] = t_str
            print(f"✅ Added: {day_name} at {t_str}\n")
    else:
        new_sched = {k: v for k, v in sched.items() if not k.startswith("_")}
        
    print("\n⚙️ Settings")
    rec_vid = get_input("Record Video? (1=Yes, 0=No)", "1" if target[6] else "0") == "1"
    rec_aud = get_input("Record Audio? (1=Yes, 0=No)", "1" if target[7] else "0") == "1"
    
    settings = sched.get("_settings", {})
    pause_sec = get_input("Pause record if silence (sec)", settings.get("pause_sec", "60"))
    silence = get_input("Exit completely if silence (mins)", str(target[9]))
    max_dur = get_input("Max Class Duration (mins)", settings.get("max_dur", "90"))
    save_path = get_input("Save Path", target[8])
    
    new_sched["_settings"] = {
        "pause_sec": pause_sec,
        "max_dur": max_dur,
        "ignore_next": settings.get("ignore_next", False)
    }
    
    data = (user_name, password, class_name, link, json.dumps(new_sched), int(rec_vid), int(rec_aud), save_path, int(silence))
    database.update_class(class_id, data)
    print(f"\n✅ Class '{class_name}' updated successfully!\n")

def set_ignore_status(class_id, is_ignored):
    classes = database.get_classes()
    target = next((c for c in classes if c[0] == class_id), None)
    
    if not target:
        print(f"\n❌ Class ID {class_id} not found.\n")
        return
        
    try:
        sched = json.loads(target[5])
    except:
        sched = {}
        
    settings = sched.get("_settings", {})
    settings["ignore_next"] = is_ignored
    sched["_settings"] = settings
    
    data = (target[1], target[2], target[3], target[4], json.dumps(sched), target[6], target[7], target[8], target[9])
    database.update_class(class_id, data)
    
    state_str = "IGNORED (Skip Next)" if is_ignored else "RESTORED (Active)"
    print(f"\n✅ Class '{target[3]}' next session is now {state_str}.\n")

def join_class(class_id):
    classes = database.get_classes()
    target = next((c for c in classes if c[0] == class_id), None)
    
    if not target:
        print(f"\n❌ Class ID {class_id} not found.\n")
        return
        
    print_banner()
    print(f"🚀 Manually joining class: {target[3]}")
    print("Press Ctrl+C at any time to gracefully stop the bot and save files.\n")
    
    try:
        bot = SkyroomClassBot(target)
        bot.start()
        # حلقه بی‌نهایت برای باز نگه داشتن ترمینال تا زمانی که ربات در حال اجراست
        while bot.is_running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⏹️ User interrupted. Stopping bot and saving files safely...")
        bot.stop_all()

def delete_class(class_id):
    classes = database.get_classes()
    exists = any(c[0] == class_id for c in classes)
    
    if exists:
        database.delete_class(class_id)
        print(f"\n🗑️ Class ID {class_id} deleted successfully.\n")
    else:
        print(f"\n❌ Class ID {class_id} not found.\n")


def run_cli_scheduler():
    print_banner()
    print("🕒 Starting CLI Background Scheduler...")
    print("Keeping terminal open to monitor schedule. Press Ctrl+C to stop.\n")
    
    active_bots = []
    
    try:
        while True:
            now = time.localtime()
            current_time = time.strftime("%H:%M", now)
            current_day = time.strftime("%A", now)
            
            classes = database.get_classes()
            for cls in classes:
                try:
                    schedule_dict = json.loads(cls[5])
                    if current_day in schedule_dict and schedule_dict[current_day] == current_time:
                        
                        settings = schedule_dict.get("_settings", {})
                        if settings.get("ignore_next", False):
                            app_logger.info(f"Skipping ignored session for class: {cls[3]}")
                            settings["ignore_next"] = False
                            schedule_dict["_settings"] = settings
                            database.update_class(cls[0], (cls[1], cls[2], cls[3], cls[4], json.dumps(schedule_dict), cls[6], cls[7], cls[8], cls[9]))
                            continue 
                        
                        app_logger.info(f"Schedule matched! Initializing bot for class: {cls[3]}")
                        
                        for active_bot in active_bots:
                            if active_bot.is_running:
                                app_logger.info("Terminating previous class session to prevent overlap.")
                                active_bot.stop_all()
                        
                        active_bots.clear() 

                        bot = SkyroomClassBot(cls)
                        active_bots.append(bot)
                        bot.start()
                        time.sleep(60) 
                except Exception as e:
                    app_logger.error(f"Error in scheduler loop: {e}", exc_info=True)
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Scheduler stopped by user. Cleaning up...")
        for bot in active_bots:
            if bot.is_running:
                bot.stop_all()



def main():
    parser = argparse.ArgumentParser(
        description="Skyroom Auto-Attend CLI Manager",
        epilog="Use 'python3 cli.py <command> -h' for more info on a specific command."
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    subparsers.add_parser("add", help="Add a new class interactively")
    subparsers.add_parser("list", help="List all scheduled classes and their status")

    subparsers.add_parser("start-scheduler", help="Run the background scheduler in the terminal (Keeps terminal open)")
    
    join_parser = subparsers.add_parser("join", help="Join a class immediately by its ID")
    join_parser.add_argument("id", type=int, help="The ID of the class to join")
    
    ignore_parser = subparsers.add_parser("ignore", help="Toggle 'Ignore Next Session' for a class")
    ignore_parser.add_argument("id", type=int, help="The ID of the class to ignore/restore")
    restore_parser = subparsers.add_parser("restore", help="Restore an ignored class (Make it Active)")
    restore_parser.add_argument("id", type=int, help="The ID of the class to restore")
    
    edit_parser = subparsers.add_parser("edit", help="Edit an existing class by its ID")
    edit_parser.add_argument("id", type=int, help="The ID of the class to edit")
    
    del_parser = subparsers.add_parser("delete", help="Delete a class by its ID")
    del_parser.add_argument("id", type=int, help="The ID of the class to delete")

    args = parser.parse_args()
    database.init_db()

    if args.command == "add":
        add_class()
    elif args.command == "list":
        list_classes()
    elif args.command == "join":
        join_class(args.id)
    elif args.command == "ignore":
        set_ignore_status(args.id, True)
    elif args.command == "restore":
        set_ignore_status(args.id, False)
    elif args.command == "edit":
        edit_class(args.id)
    elif args.command == "delete":
        delete_class(args.id)
    elif args.command == "start-scheduler":
        run_cli_scheduler()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

import os
import csv
from datetime import datetime
from pathlib import Path
from dashboard.utils.attendance import should_auto_checkout, get_shift_status

def auto_checkout():
    """
    Automatically check out users at the end of their shift
    """
    try:
        # Get today's attendance file
        current_date = datetime.now().strftime("%y_%m_%d")
        attendance_file = Path("Attendance_Entry") / f"Attendance_{current_date}.csv"
        
        if not attendance_file.exists():
            print(f"No attendance file found for {current_date}")
            return
            
        # Read current attendance
        with open(attendance_file, 'r') as f:
            reader = csv.DictReader(f)
            records = list(reader)
            
        # Group by name to get latest action for each user
        users_to_checkout = {}
        for record in records:
            name = record["Name"]
            action = record["Action"]
            time_str = f"{record['Date']} {record['Time']}"
            checkin_time = datetime.strptime(time_str, "%y_%m_%d %H:%M:%S")
            
            if action == "checkin":
                users_to_checkout[name] = checkin_time
            elif action == "checkout":
                if name in users_to_checkout:
                    del users_to_checkout[name]
                    
        # Check out users whose shift has ended
        now = datetime.now()
        for name, checkin_time in users_to_checkout.items():
            if should_auto_checkout(checkin_time, now):
                shift, _ = get_shift_status(checkin_time)
                
                # Add checkout record
                with open(attendance_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        name,
                        now.strftime("%H:%M:%S"),
                        current_date,
                        "checkout",
                        "auto",
                        shift
                    ])
                print(f"Auto checked out {name} at {now.strftime('%H:%M:%S')}")
                
    except Exception as e:
        print(f"Error in auto checkout: {e}")

if __name__ == "__main__":
    auto_checkout()
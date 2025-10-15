import streamlit as st
from pathlib import Path
import subprocess
import time
import sys
import os
import csv
from datetime import datetime
from utils import sound

def get_current_root_dir():
    """Get the root directory where main.py is located"""
    return Path(__file__).parent.parent.parent

def get_current_attendance():
    """Get today's attendance records"""
    try:
        current_date = datetime.now().strftime("%y_%m_%d")
        attendance_file = get_current_root_dir() / "Attendance_Entry" / f"Attendance_{current_date}.csv"
        
        if not attendance_file.exists():
            return []
            
        with open(attendance_file, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        print(f"Error reading attendance: {e}")
        return []

def check_registration():
    """Check if any users are registered in the system"""
    attendance_dir = get_current_root_dir() / "Attendance_data"
    if not attendance_dir.exists():
        return False
    
    # Check for any user folders
    user_folders = [f for f in attendance_dir.iterdir() if f.is_dir()]
    return len(user_folders) > 0

def start_attendance(mode="checkin"):
    """Start the attendance process"""
    try:
        # Get root directory
        root_dir = get_current_root_dir()
        script_path = root_dir / "main.py"
        
        if not script_path.exists():
            st.error(f"❌ Script absensi tidak ditemukan di: {script_path}")
            return False
            
        # Make sure we're using the root Attendance_data folder
        attendance_dir = root_dir / "Attendance_data"
        if not attendance_dir.exists() or not any(attendance_dir.iterdir()):
            st.error("❌ Tidak ada user terdaftar di sistem")
            return False
            
        # Kill any existing python processes running main.py
        import psutil
        PROCNAME = "python.exe"
        for proc in psutil.process_iter():
            try:
                if proc.name() == PROCNAME:
                    cmdline = proc.cmdline()
                    if len(cmdline) > 1 and "main.py" in cmdline[1]:
                        proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        # Set up environment
        env = os.environ.copy()
        env['PYTHONPATH'] = str(root_dir)
        
        # Start attendance process with mode
        process = subprocess.Popen(
            [sys.executable, str(script_path), mode],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            cwd=str(root_dir),
            env=env,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        return process
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None

def get_shift_status(recognized_name):
    """
    Get user's shift and attendance status
    Returns: (assigned_shift, current_shift, status, is_checkout)
    """
    now = datetime.now()
    current_hour = now.hour
    
    # Define shift times
    morning_start = 8    # 08:00
    morning_end = 17     # 17:00
    night_start = 17     # 17:00
    night_end = 22      # 22:00
    
    # Toleransi untuk shift malam yang datang lebih awal
    night_early_start = 16  # Boleh datang 1 jam sebelum shift
    
    # Determine current shift
    if morning_start <= current_hour < morning_end:
        current_shift = "morning"
    elif night_early_start <= current_hour <= night_end:  # Diperluas untuk toleransi
        current_shift = "night"
    else:
        current_shift = "outside_hours"  # Di luar jam kerja
    
    # Get user's assigned shift from registration data
    root_dir = get_current_root_dir()
    try:
        import json
        with open(root_dir / "user_data.json", "r") as f:
            user_data = json.load(f)
            if recognized_name in user_data:
                assigned_shift = user_data[recognized_name].get('shift', 'morning')
            else:
                assigned_shift = 'morning'  # default to morning if not found
    except:
        assigned_shift = 'morning'  # default to morning if file not found
        
    # Check if this is checkout time based on shift
    is_checkout = False
    if current_shift == "morning" and current_hour >= 16:  # Bisa checkout mulai 16:00
        is_checkout = True
    elif current_shift == "night" and current_hour >= 21:  # Bisa checkout mulai 21:00
        is_checkout = True
    
    # Check if already checked in today
    has_checked_in = False
    try:
        attendance_file = get_current_root_dir() / "Attendance_Entry" / f"Attendance_{now.strftime('%y_%m_%d')}.csv"
        if attendance_file.exists():
            import pandas as pd
            df = pd.read_csv(attendance_file)
            has_checked_in = recognized_name in df['Name'].values
    except:
        pass  # Assume not checked in if can't read file
    
    # Determine status based on time and check-in status
    if current_shift == "outside_hours":
        status = "outside_hours"  # Di luar jam kerja
    elif is_checkout:
        if not has_checked_in:
            status = "no_checkin"  # Trying to checkout without checkin
        else:
            status = "checkout"
    else:
        # For check-in
        if has_checked_in:
            status = "already_checkedin"
        else:
            # Cek kesesuaian shift
            shift_match = assigned_shift == current_shift
            
            if current_shift == "morning" and assigned_shift == "night":
                status = "wrong_shift"  # User shift malam mencoba absen di pagi hari
            elif current_shift == "night" and assigned_shift == "morning":
                # Toleransi khusus untuk shift pagi yang lembur/overlap ke shift malam
                if current_hour < night_start:  # Sebelum jam 17:00
                    status = "overtime_checkin"
                else:
                    status = "wrong_shift"
            else:
                # Normal check-in sesuai shift
                if current_shift == "morning":
                    status = "on_time" if current_hour <= 8 else "late"
                else:  # night shift
                    # Toleransi untuk shift malam yang datang lebih awal
                    status = "on_time" if current_hour <= 17 else "late"
        
    return assigned_shift, current_shift, status, is_checkout

def check_attendance_status(process):
    """
    Check attendance process status
    """
    if not process:
        return False, "Process not found"
        
    try:
        # Check if process has already terminated
        if hasattr(process, '_terminated') and process._terminated:
            return False, "✅ Absensi selesai"
            
        poll_result = process.poll()
        
        if poll_result is None:  # Still running
            stdout_lines = []
            if process.stdout:
                line = process.stdout.readline()
                if line:
                    stdout_lines.append(line.strip())
                    
            # Get latest output
            latest_output = stdout_lines[-1] if stdout_lines else ""
            
            # Check for recognized face
            if "Recognized:" in latest_output:
                # Extract name and get shift info
                recognized_name = latest_output.split("Recognized:")[1].strip()
                assigned_shift, current_shift, status, is_checkout = get_shift_status(recognized_name)
                
                # Record attendance first
                now = datetime.now()
                attendance_file = get_current_root_dir() / "Attendance_Entry" / f"Attendance_{now.strftime('%y_%m_%d')}.csv"
                
                # Ensure directory exists
                attendance_file.parent.mkdir(exist_ok=True)
                
                # Create or append to CSV
                file_exists = attendance_file.exists()
                with open(attendance_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(["Name", "Time", "Date", "Shift", "Status"])
                    writer.writerow([
                        recognized_name,
                        now.strftime('%H:%M:%S'),
                        now.strftime('%Y-%m-%d'),
                        current_shift,
                        status
                    ])
                
                # Close camera after recognition
                process.terminate()
                
                # Prepare status message based on attendance type and status
                message = ""
                if status == "outside_hours":
                    message = f"❌ Di luar jam kerja!\nNama: {recognized_name}\n\nJam kerja:\nShift Pagi: 08:00 - 17:00\nShift Malam: 17:00 - 22:00"
                elif status == "wrong_shift":
                    message = (f"⚠️ Ketidaksesuaian Shift!\n"
                             f"Nama: {recognized_name}\n"
                             f"Anda terdaftar di shift {assigned_shift.upper()}\n"
                             f"Jam kerja Anda:\n"
                             f"{'08:00 - 17:00' if assigned_shift == 'morning' else '17:00 - 22:00'}")
                elif status == "overtime_checkin":
                    message = (f"⚠️ Perhatian - Overtime Check-in\n"
                             f"Nama: {recognized_name}\n"
                             f"Anda melakukan check-in di luar shift normal Anda (Shift {assigned_shift.upper()})\n"
                             f"Absensi akan dicatat sebagai overtime/lembur.")
                    sound.play_sound('notification')
                elif status == "no_checkin":
                    message = f"❌ Tidak dapat melakukan checkout!\nNama: {recognized_name}\nAnda belum melakukan check-in hari ini."
                elif status == "already_checkedin":
                    message = f"⚠️ Sudah absen masuk!\nNama: {recognized_name}\nSilakan lakukan checkout di jam pulang."
                elif status == "checkout":
                    message = f"✅ Checkout berhasil!\nNama: {recognized_name}\nTerima kasih atas kerja kerasnya hari ini!"
                    sound.play_sound('success')
                else:
                    time_status = "tepat waktu" if status == "on_time" else "terlambat"
                    shift_info = ""
                    if assigned_shift != current_shift and status != "overtime_checkin":
                        shift_info = f"\n⚠️ Anda terdaftar di shift {assigned_shift} tapi melakukan absensi di shift {current_shift}"
                    
                    batas_telat = "08:00" if current_shift == "morning" else "17:00"
                    message = f"✅ Check-in berhasil!\nNama: {recognized_name}\nStatus: {time_status} (Batas: {batas_telat}){shift_info}"
                    if status == "on_time":
                        sound.play_sound('success')
                    else:
                        sound.play_sound('notification')
                
                return False, message
                
            # Check for recognized face processing
            if "Recognized" in latest_output:
                return True, "✅ Wajah terdeteksi"
                
            return True, "🎥 Menunggu wajah terdeteksi..."
            
        else:  # Process finished
            stdout, stderr = process.communicate()
            if poll_result == 0:
                return False, "✅ Absensi selesai"
            else:
                return False, f"❌ Error: {stderr if stderr else 'Unknown error'}"
                
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

def show_attendance():
    """Show attendance capture page"""
    st.header("Face Recognition Attendance")
    
    # Check if users are registered
    if not check_registration():
        st.warning("⚠️ Belum ada user yang terdaftar. Silakan registrasi user terlebih dahulu di menu Register New User.")
        if st.button("Ke Halaman Registrasi", type="primary"):
            st.session_state['current_page'] = "Register New User"
            st.rerun()
        return
    
    # Create tabs for attendance actions and history
    tab1, tab2 = st.tabs(["Absensi", "Riwayat Absensi"])
    
    with tab1:
        st.write("Gunakan halaman ini untuk melakukan absensi menggunakan face recognition.")
        
        # Initialize state if not exists
        if 'attendance_state' not in st.session_state:
            st.session_state['attendance_state'] = {
                'is_running': False,
                'process': None,
                'last_captured': None
            }
        
        state = st.session_state.attendance_state
        
        # Show attendance button if not running
        if not state['is_running']:
            if st.button("Mulai Absensi", type="primary", width="stretch"):
                process = start_attendance()
                if process:
                    state['is_running'] = True
                    state['process'] = process
                    state['last_captured'] = None
                    st.rerun()
        
        # Show status if running
        else:
            st.info("🎥 Proses absensi sedang berjalan...")
    
    with tab2:
        st.subheader("Riwayat Absensi")
        
        # Date selector for attendance history
        col1, col2 = st.columns([2,2])
        with col1:
            selected_date = st.date_input(
                "Pilih Tanggal",
                datetime.now()
            )
        
        # Format date for filename
        date_str = selected_date.strftime("%y_%m_%d")
        attendance_file = get_current_root_dir() / "Attendance_Entry" / f"Attendance_{date_str}.csv"
        
        if attendance_file.exists():
            # Read and display attendance data
            try:
                import pandas as pd
                df = pd.read_csv(attendance_file)
                
                # Convert time to datetime if needed
                if 'Time' in df.columns:
                    df['Time'] = pd.to_datetime(df['Time']).dt.strftime('%H:%M:%S')
                
                # Display the attendance records in a table
                st.dataframe(
                    df,
                    column_config={
                        "Name": "Nama",
                        "Time": "Waktu",
                        "Date": "Tanggal"
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # Show summary metrics
                total_records = len(df)
                if total_records > 0:
                    st.write(f"Total absensi hari ini: {total_records}")
                    
                    # If we have shift information
                    if 'Shift' in df.columns:
                        shifts = df['Shift'].value_counts()
                        st.write("Breakdown per shift:")
                        for shift, count in shifts.items():
                            st.write(f"- {shift.title()}: {count}")
            except Exception as e:
                st.error(f"Error membaca data absensi: {str(e)}")
        else:
            st.info(f"Tidak ada data absensi untuk tanggal {selected_date.strftime('%d-%m-%Y')}")
        
        # Add cancel button
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("❌ Batalkan", width="stretch"):
                if state['process']:
                    state['process'].terminate()
                state['is_running'] = False
                state['process'] = None
                st.rerun()
        
        # Check process status
        is_running, status = check_attendance_status(state['process'])
        
        if not is_running:
            if "berhasil" in status.lower():
                st.success(status)
            elif "error" in status.lower():
                st.error(status)
            else:
                st.info(status)
            
            # Reset state after showing status
            time.sleep(2)
            state['is_running'] = False
            state['process'] = None
            st.rerun()
        else:
            st.info(status)
            
    # Show attendance history
    st.divider()
    st.subheader("Riwayat Absensi Hari Ini")
    
    try:
        attendance_file = get_current_root_dir() / "Attendance_Entry" / f"Attendance_{datetime.now().strftime('%y_%m_%d')}.csv"
        if attendance_file.exists():
            import pandas as pd
            df = pd.read_csv(attendance_file)
            if not df.empty:
                st.dataframe(df, width="stretch")
            else:
                st.info("Belum ada absensi hari ini")
        else:
            st.info("Belum ada absensi hari ini")
    except Exception as e:
        st.error(f"Error membaca riwayat absensi: {str(e)}")
import streamlit as st
from pathlib import Path
import subprocess
import time
import sys
import os
import csv
import pandas as pd
import cv2
import numpy as np
from datetime import datetime
from utils import sound
from utils.face_recognition_utils import (
    get_camera_feed,
    analyze_face_image, 
    load_face_encodings,
    initialize_attendance_state,
    reset_attendance_state,
    record_attendance
)

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
    """
    This is a placeholder function to maintain compatibility with existing code.
    The actual attendance is now handled directly within the Streamlit interface.
    """
    return True

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

def process_recognized_face(recognized_name):
    """
    Process a recognized face and record attendance
    
    Args:
        recognized_name: Name of the recognized person
        
    Returns:
        str: Status message to display
    """
    try:
        # Get shift status
        assigned_shift, current_shift, status, is_checkout = get_shift_status(recognized_name)
        
        # Record attendance
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
                
        return message
    except Exception as e:
        return f"❌ Error: {str(e)}"

def show_attendance():
    """Show attendance capture page"""
    st.header("Face Recognition Attendance")
    
    # Import camera utilities
    from utils.camera import get_camera_feed, analyze_face_image, load_face_encodings
    
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
        
        # Initialize attendance state
        state = initialize_attendance_state()
        
        # Get known face encodings
        known_face_encodings, known_face_names = load_face_encodings()
        
        if len(known_face_encodings) == 0:
            st.warning("⚠️ No face encodings found. Please register users first.")
        else:
            # Layout with camera controls
            control_col1, control_col2, control_col3 = st.columns(3)
            
            with control_col1:
                if st.button("📸 Start Recognition", type="primary"):
                    state['camera_active'] = True
                    state['is_active'] = True
            
            with control_col2:
                if st.button("⏹️ Stop Camera", type="secondary"):
                    state['camera_active'] = False
                    state['is_active'] = False
                    
            with control_col3:
                if st.button("🔄 Reset", type="secondary"):
                    reset_attendance_state()
                    st.rerun()
            
            # Camera display and info in two columns
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Camera container
                camera_container = st.empty()
                status_container = st.empty()
                
                # Either show camera feed or camera component based on active state
                if state['camera_active']:
                    # Get camera feed via camera_input
                    camera_image = get_camera_feed()
                    
                    # Process camera feed if image was captured
                    if camera_image is not None:
                        # Convert the image from bytes to an OpenCV image
                        bytes_data = camera_image.getvalue()
                        img_array = np.frombuffer(bytes_data, np.uint8)
                        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                        
                        # Analyze face in the image
                        results = analyze_face_image(image, known_face_encodings, known_face_names)
                        
                        # Show recognition status
                        if results and results['face_detected']:
                            if results['multiple_faces']:
                                status_container.warning("⚠️ Multiple faces detected! Please ensure only one person is in frame.")
                            elif results['recognized_name']:
                                recognized_name = results['recognized_name']
                                
                                # Check if this is a new recognition (not in cooldown)
                                current_time = time.time()
                                cooldown_expired = (
                                    state['recognition_time'] is None or
                                    current_time - state['recognition_time'] > 5  # 5 seconds cooldown
                                )
                                
                                if (state['last_recognized'] != recognized_name) or cooldown_expired:
                                    # New person or cooldown expired
                                    status_message = process_recognized_face(recognized_name)
                                    
                                    # Update state
                                    state['last_recognized'] = recognized_name
                                    state['recognition_time'] = current_time
                                    state['status_message'] = status_message
                                    
                                    # Record the user as recognized
                                    if 'recognized_users' not in state:
                                        state['recognized_users'] = []
                                    if recognized_name not in state['recognized_users']:
                                        state['recognized_users'].append(recognized_name)
                                    
                                    # Show success message
                                    status_container.success(f"✅ Recognized: {recognized_name}")
                                    st.info(status_message)
                                else:
                                    # Still in cooldown, show previous message
                                    if state['status_message']:
                                        status_container.info(state['status_message'])
                            else:
                                status_container.warning("❓ Face detected but not recognized. Please register first.")
                        else:
                            status_container.info("🔍 No face detected. Please position your face in front of the camera.")
                else:
                    # Show placeholder when camera is inactive
                    camera_container.info("📸 Click the 'Start Recognition' button to activate the camera.")
            
            with col2:
                st.subheader("Recognized Users")
                
                # Show recognized users
                if 'recognized_users' in state and state['recognized_users']:
                    for user in state['recognized_users']:
                        st.success(f"✅ {user}")
                else:
                    st.info("No users recognized yet.")
                
                st.markdown("---")
                st.subheader("Instructions")
                st.markdown("""
                1. Click **Start Recognition** to activate camera
                2. Position your face in frame
                3. Wait for successful recognition
                4. Attendance will be recorded automatically
                """)
                
                # Today's stats
                st.markdown("---")
                st.subheader("Today's Status")
                
                # Read today's attendance for quick stats
                try:
                    attendance_file = get_current_root_dir() / "Attendance_Entry" / f"Attendance_{datetime.now().strftime('%y_%m_%d')}.csv"
                    if attendance_file.exists():
                        df = pd.read_csv(attendance_file)
                        st.metric("Total Records", len(df))
                        
                        # Show check-ins vs check-outs if Status column exists
                        if 'Status' in df.columns:
                            checkins = len(df[df['Status'] == 'Check-In'])
                            checkouts = len(df[df['Status'] == 'Check-Out'])
                            st.metric("Check-ins", checkins)
                            st.metric("Check-outs", checkouts)
                    else:
                        st.info("No attendance recorded today")
                except Exception as e:
                    st.error(f"Error loading stats: {str(e)}")
    
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
                df = pd.read_csv(attendance_file)
                
                # Convert time to datetime if needed
                if 'Time' in df.columns:
                    df['Time'] = pd.to_datetime(df['Time']).dt.strftime('%H:%M:%S')
                
                # Calculate metrics
                total_records = len(df)
                unique_users = df['Name'].nunique()
                
                # Display metrics in a visually appealing way
                metrics_cols = st.columns(3)
                with metrics_cols[0]:
                    st.metric("Total Absensi", total_records)
                with metrics_cols[1]:
                    st.metric("Jumlah User", unique_users)
                
                if 'Status' in df.columns:
                    status_counts = df['Status'].value_counts().to_dict()
                    with metrics_cols[2]:
                        checkins = status_counts.get('Check-In', 0)
                        checkouts = status_counts.get('Check-Out', 0)
                        st.metric("Check-In/Out", f"{checkins}/{checkouts}")
                
                # Display the attendance records in a table with enhanced column config
                st.dataframe(
                    df,
                    column_config={
                        "Name": st.column_config.TextColumn("Nama", help="Nama pengguna"),
                        "Time": st.column_config.TextColumn("Waktu", help="Waktu absensi"),
                        "Date": st.column_config.TextColumn("Tanggal", help="Tanggal absensi"),
                        "Status": st.column_config.TextColumn("Status", help="Status absensi (Check-In/Check-Out)"),
                        "Shift": st.column_config.TextColumn("Shift", help="Shift kerja (pagi/malam)") if 'Shift' in df.columns else None
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # Visualizations for better data analysis
                if total_records > 0:
                    st.subheader("Analisis Absensi")
                    
                    # User breakdown chart
                    user_counts = df['Name'].value_counts().reset_index()
                    user_counts.columns = ['User', 'Count']
                    st.subheader("Breakdown per User")
                    st.bar_chart(user_counts, x='User', y='Count')
                    
                    # If we have shift information
                    if 'Shift' in df.columns:
                        shift_counts = df['Shift'].value_counts().reset_index()
                        shift_counts.columns = ['Shift', 'Count']
                        
                        cols = st.columns(2)
                        with cols[0]:
                            st.subheader("Breakdown per Shift")
                            st.bar_chart(shift_counts, x='Shift', y='Count')
                        
                        # If we have status information as well
                        if 'Status' in df.columns:
                            status_counts = df['Status'].value_counts().reset_index()
                            status_counts.columns = ['Status', 'Count']
                            
                            with cols[1]:
                                st.subheader("Breakdown per Status")
                                st.bar_chart(status_counts, x='Status', y='Count')
            except Exception as e:
                st.error(f"Error membaca data absensi: {str(e)}")
        else:
            st.info(f"Tidak ada data absensi untuk tanggal {selected_date.strftime('%d-%m-%Y')}")
            
    # Redundant section removed
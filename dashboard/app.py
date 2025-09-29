import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
import time
from pathlib import Path
import os
import sys
import subprocess
import shutil

# Configure page
st.set_page_config(
    page_title="Face Recognition Attendance Dashboard",
    page_icon="📊",
    layout="wide"
)

# API endpoints
API_URL = "http://localhost:8000"
TOKEN_KEY = "access_token"

def api_call(endpoint: str, method="get", **kwargs):
    try:
        url = f"{API_URL}{endpoint}"
        if method.lower() == "get":
            response = requests.get(url, **kwargs)
        else:
            response = requests.post(url, **kwargs)
            
        if response.status_code != 200:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
            
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Tidak dapat terhubung ke server. Pastikan server API sedang berjalan.")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def get_today_attendance():
    try:
        response = api_call("/attendance/today")
        if response and "data" in response:
            df = pd.DataFrame(response["data"])
            # Jika df tidak kosong tapi tidak memiliki kolom yang diperlukan, tambahkan dengan nilai default
            if not df.empty:
                if 'shift' not in df.columns:
                    df['shift'] = 'morning'  # default shift
                if 'status' not in df.columns:
                    df['status'] = 'on_time'  # default status
            return df
        return pd.DataFrame(columns=['employee_name', 'shift', 'status', 'check_in', 'check_out'])
    except:
        st.error("Gagal mengambil data absensi hari ini")
        return pd.DataFrame(columns=['employee_name', 'shift', 'status', 'check_in', 'check_out'])

def get_all_attendance():
    try:
        response = api_call("/attendance/all")
        if response and 'data' in response:
            return pd.DataFrame(response['data'])
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Failed to fetch attendance data: {str(e)}")
        return pd.DataFrame()

def get_registered_users():
    try:
        response = api_call("/users")
        if response and "data" in response:
            # Sort users by name
            users = sorted(response["data"], key=lambda x: x["name"].lower())
            # Log the users for debugging
            print("Retrieved users:", users)
            return users
        print("No data in response or invalid response:", response)
        return []
    except Exception as e:
        st.error(f"Failed to fetch registered users: {str(e)}")
        return []

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = 'Overview'
if 'registration_state' not in st.session_state:
    st.session_state['registration_state'] = {
        'is_registering': False,
        'current_step': 0,
        'user_data': None,
        'process': None,
        'error': None
    }

def navigate_to(page_name):
    st.session_state['current_page'] = page_name
    # Reset registration state when navigating away from registration
    if page_name != 'Register New User':
        st.session_state['registration_state'] = {
            'is_registering': False,
            'current_step': 0,
            'user_data': None,
            'process': None,
            'error': None
        }
    
# Main dashboard
def main():
    st.title("Face Recognition Attendance Dashboard")
    
    # Sidebar
    st.sidebar.title("Navigation")
    
    # Navigation options
    pages = ["Overview", "Daily Statistics", "User Management", "Register New User"]
    
    # Use session state for the radio button
    current_page_index = pages.index(st.session_state['current_page'])
    selected_page = st.sidebar.radio("Choose a page", pages, index=current_page_index)
    
    # Update session state if page changes
    if selected_page != st.session_state['current_page']:
        st.session_state['current_page'] = selected_page
        st.rerun()
        
    # Route to appropriate page
    if st.session_state['current_page'] == "Overview":
        show_overview()
    elif st.session_state['current_page'] == "Daily Statistics":
        show_daily_statistics()
    elif st.session_state['current_page'] == "User Management":
        show_user_management()
    elif st.session_state['current_page'] == "Register New User":
        show_user_registration()

def show_overview():
    st.header("Overview Hari Ini")
    
    # Get today's data and device status
    df = get_today_attendance()
    response = api_call("/devices")
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_present = len(df) if not df.empty else 0
    with col1:
        st.metric("Total Hadir", total_present)
    
    # Initialize counters
    morning_count = 0
    night_count = 0
    
    if not df.empty and 'shift' in df.columns:
        morning_shift = df[df['shift'] == 'morning']
        night_shift = df[df['shift'] == 'night']
        
        morning_count = len(morning_shift)
        night_count = len(night_shift)
    
    with col2:
        st.metric("Shift Pagi", morning_count)
    with col3:
        st.metric("Shift Malam", night_count)
    
    # Get device status
    devices = response.get('data', []) if response else []
    active_devices = 0
    if devices:
        active_devices = sum(1 for device in devices if isinstance(device, dict) and device.get('status') == 'active')
    
    with col4:
        st.metric("Perangkat Aktif", active_devices)
    
    # Display shift details
    st.subheader("Today's Attendance by Shift")
    if not df.empty:
        tabs = st.tabs(["Morning Shift", "Night Shift"])
        
        with tabs[0]:
            morning_df = df[df['shift'] == 'morning']
            if not morning_df.empty:
                on_time = len(morning_df[morning_df['status'] == 'on_time'])
                late = len(morning_df[morning_df['status'] == 'late'])
                invalid = len(morning_df[morning_df['status'] == 'invalid'])
                
                mcol1, mcol2, mcol3 = st.columns(3)
                with mcol1:
                    st.metric("On Time", on_time)
                with mcol2:
                    st.metric("Late", late)
                with mcol3:
                    st.metric("Invalid", invalid)
                    
                st.dataframe(morning_df[['employee_name', 'check_in', 'check_out', 'status']])
            else:
                st.info("No morning shift attendance yet")
        
        with tabs[1]:
            night_df = df[df['shift'] == 'night']
            if not night_df.empty:
                on_time = len(night_df[night_df['status'] == 'on_time'])
                late = len(night_df[night_df['status'] == 'late'])
                invalid = len(night_df[night_df['status'] == 'invalid'])
                
                ncol1, ncol2, ncol3 = st.columns(3)
                with ncol1:
                    st.metric("On Time", on_time)
                with ncol2:
                    st.metric("Late", late)
                with ncol3:
                    st.metric("Invalid", invalid)
                    
                st.dataframe(night_df[['employee_name', 'check_in', 'check_out', 'status']])
            else:
                st.info("No night shift attendance yet")
    else:
        st.info("No attendance records for today yet")
    
    # Display device status
    if devices:
        st.subheader("Device Status")
        device_df = pd.DataFrame(devices)
        device_df['last_active'] = pd.to_datetime(device_df['last_active'])
        
        # Add status indicators
        def get_status_color(status):
            return '🟢' if status == 'active' else '🔴'
            
        device_df['indicator'] = device_df['status'].apply(get_status_color)
        device_df['last_active'] = device_df['last_active'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        st.dataframe(device_df[['indicator', 'device_id', 'name', 'location', 'last_active', 'status']])

def show_daily_statistics():
    st.header("Daily Statistics")
    
    df = get_all_attendance()
    if not df.empty:
        # Check and rename columns if needed
        date_column = 'date' if 'date' in df.columns else 'Date'
        time_column = 'time' if 'time' in df.columns else 'Time'
        
        if date_column not in df.columns:
            st.error("Date column not found in the data")
            st.write("Available columns:", df.columns.tolist())
            return
            
        df[date_column] = pd.to_datetime(df[date_column])
        daily_counts = df.groupby(date_column).size().reset_index(name='count')
        
        fig = px.line(daily_counts, x=date_column, y='count', 
                     title='Daily Attendance Trends')
        st.plotly_chart(fig)
        
        # Attendance by hour
        if time_column in df.columns:
            df['Hour'] = pd.to_datetime(df[time_column]).dt.hour
            hourly_counts = df.groupby('Hour').size().reset_index(name='count')
            
            fig2 = px.bar(hourly_counts, x='Hour', y='count',
                         title='Attendance by Hour of Day')
            st.plotly_chart(fig2)
    else:
        st.info("No attendance data available")

def show_user_management():
    st.header("User Management")
    
    # Get registered users from API
    users_response = api_call("/users")
    registered_users = []
    if users_response and "data" in users_response:
        registered_users = users_response["data"]

    if registered_users:
        # CSS untuk styling
        st.markdown("""
        <style>
        .user-card {
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 1rem;
            text-align: center;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
            height: 100%;
        }
        .user-name {
            font-size: 1.2rem;
            font-weight: bold;
            margin: 0.5rem 0;
            color: #2C3E50;
            text-transform: capitalize;
        }
        .user-info {
            color: #666;
            font-size: 0.9rem;
            margin: 0.3rem 0;
        }
        .status-active {
            color: #4CAF50;
            font-weight: bold;
            margin-top: 0.5rem;
        }
        .image-type {
            background-color: #f0f0f0;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            color: #666;
            margin-top: 0.5rem;
            display: inline-block;
        }
        </style>
        """, unsafe_allow_html=True)

        # Header dengan jumlah user
        st.subheader(f"Daftar User Terdaftar (Total: {len(registered_users)})")
        
        # Pisahkan users berdasarkan tipe gambar
        single_image_users = []
        multiple_image_users = []
        
        for user in registered_users:
            user_name = user["name"]
            attendance_data_path = Path(__file__).parent.parent / "Attendance_data"
            single_image = attendance_data_path / f"{user_name}.png"
            folder_image = attendance_data_path / user_name / "center.png"
            
            if single_image.exists():
                single_image_users.append({"user": user, "image_path": single_image})
            elif folder_image.exists():
                multiple_image_users.append({"user": user, "image_path": folder_image})
        
        # Tab untuk memisahkan Single Image dan Multiple Image
        tab1, tab2 = st.tabs(["Single Image Users", "Multiple Image Users"])
        
        with tab1:
            if single_image_users:
                cols = st.columns(4)
                for idx, item in enumerate(single_image_users):
                    user = item["user"]
                    image_path = item["image_path"]
                    col = cols[idx % 4]
                    with col:
                        with st.container():
                            # Card container
                            st.markdown('<div class="user-card">', unsafe_allow_html=True)
                            st.image(str(image_path), width=150)
                            st.markdown(f'<div class="user-name">{user["name"]}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="user-info">{user.get("role", "Employee").title()}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="user-info">Shift {user.get("shift", "Not Set").title()}</div>', unsafe_allow_html=True)
                            st.markdown('<div class="status-active">● Active</div>', unsafe_allow_html=True)
                            st.markdown('<div class="image-type">Single Image</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("Tidak ada user dengan single image")
                
        with tab2:
            if multiple_image_users:
                cols = st.columns(4)
                for idx, item in enumerate(multiple_image_users):
                    user = item["user"]
                    image_path = item["image_path"]
                    col = cols[idx % 4]
                    with col:
                        with st.container():
                            # Card container
                            st.markdown('<div class="user-card">', unsafe_allow_html=True)
                            st.image(str(image_path), width=150)
                            st.markdown(f'<div class="user-name">{user["name"]}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="user-info">{user.get("role", "Employee").title()}</div>', unsafe_allow_html=True)
                            st.markdown(f'<div class="user-info">Shift {user.get("shift", "Not Set").title()}</div>', unsafe_allow_html=True)
                            st.markdown('<div class="status-active">● Active</div>', unsafe_allow_html=True)
                            st.markdown('<div class="image-type">Multiple Images</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("Tidak ada user dengan multiple images")

    else:
        # Tampilkan pesan jika tidak ada user
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.warning("Belum ada user terdaftar.")
            st.markdown("Klik tombol di bawah untuk menambahkan user baru.")
    
    # Tombol registrasi
    st.markdown("---")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("""
        <style>
        div.stButton > button {
            background-color: #4CAF50;
            color: white;
            padding: 15px;
            font-size: 16px;
            border-radius: 10px;
            font-weight: bold;
            border: none;
            width: 100%;
        }
        div.stButton > button:hover {
            background-color: #45a049;
        }
        </style>
        """, unsafe_allow_html=True)
        
        if st.button("➕ Tambah User Baru", use_container_width=True):
            navigate_to("Register New User")

class RegistrationError(Exception):
    """Custom exception for registration errors"""
    pass

def validate_user_input(user_data: dict) -> tuple[bool, str]:
    """
    Validate all user registration input
    Returns: (is_valid, error_message)
    """
    name = user_data.get('name', '').strip()
    
    # Validasi nama
    if not name:
        return False, "⚠️ Nama user harus diisi!"
    if len(name) < 2:
        return False, "⚠️ Nama user terlalu pendek!"
    if not name.replace(" ", "").isalnum():
        return False, "⚠️ Nama user hanya boleh mengandung huruf dan angka!"
        
    # Validasi shift
    if user_data.get('shift') not in ['morning', 'night']:
        return False, "⚠️ Shift tidak valid!"
        
    # Validasi role
    if user_data.get('role') not in ['employee', 'supervisor', 'manager']:
        return False, "⚠️ Role tidak valid!"
        
    return True, ""

def check_user_exists(name: str) -> bool:
    """
    Check if user already exists in the system
    Returns: True if user exists
    """
    attendance_dir = Path(__file__).parent.parent / "Attendance_data"
    user_file = attendance_dir / f"{name}.png"
    user_folder = attendance_dir / name
    
    return user_file.exists() or user_folder.exists()

def prepare_registration(user_data: dict) -> tuple[bool, str, subprocess.Popen]:
    """
    Prepare and start the registration process
    Returns: (success, message, process)
    """
    try:
        script_path = Path(__file__).parent.parent / "initial_data_capture.py"
        
        # Validasi script exists
        if not script_path.exists():
            raise RegistrationError(f"Script registrasi tidak ditemukan di: {script_path}")
            
        # Cek user exists
        if check_user_exists(user_data['name']):
            raise RegistrationError(f"User dengan nama '{user_data['name']}' sudah terdaftar!")
            
        # Siapkan command
        registration_cmd = [
            "cmd.exe", "/c", "start",
            sys.executable,
            str(script_path),
            user_data['name']
        ]
        
        # Jalankan proses
        process = subprocess.Popen(
            registration_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        return True, "✅ Proses registrasi dimulai!", process
        
    except RegistrationError as e:
        return False, str(e), None
    except Exception as e:
        return False, f"❌ Error tak terduga: {str(e)}", None

def get_registration_status(process: subprocess.Popen) -> tuple[bool, str]:
    """
    Check registration process status
    Returns: (is_running, status_message)
    """
    if process is None:
        return False, "Proses belum dimulai"
        
    return_code = process.poll()
    
    if return_code is None:
        return True, "Proses sedang berjalan"
    elif return_code == 0:
        return False, "Proses selesai"
    else:
        return False, f"Proses gagal dengan kode: {return_code}"
    try:
        if not script_path.exists():
            return False, f"❌ Script registrasi tidak ditemukan di: {script_path}"
        
        # Cek apakah user sudah terdaftar
        attendance_dir = script_path.parent / "Attendance_data"
        user_file = attendance_dir / f"{user_name}.png"
        user_folder = attendance_dir / user_name
        
        if user_file.exists() or user_folder.exists():
            return False, f"⚠️ User dengan nama '{user_name}' sudah terdaftar!"
            
        # Siapkan command untuk Windows
        registration_cmd = [
            "cmd.exe", "/c", "start",
            sys.executable,
            str(script_path),
            user_name
        ]
        
        process = subprocess.Popen(registration_cmd)
        time.sleep(1)  # Tunggu sebentar
        
        if process.poll() is not None:  # Proses gagal dimulai
            return False, "❌ Gagal memulai proses registrasi"
            
        return True, "✅ Proses registrasi dimulai!"
        
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

def render_registration_form() -> dict:
    """Render the registration form and return user input"""
    with st.form("user_registration", clear_on_submit=True):
        user_name = st.text_input(
            "Masukkan Nama User",
            placeholder="Contoh: John Doe",
            help="Nama harus unik dan hanya mengandung huruf dan angka"
        ).strip()
        
        col1, col2 = st.columns(2)
        with col1:
            shift = st.selectbox(
                "Pilih Shift",
                ["morning", "night"],
                help="Pilih shift kerja user"
            )
        with col2:
            role = st.selectbox(
                "Pilih Role",
                ["employee", "supervisor", "manager"],
                help="Pilih role/jabatan user"
            )
        
        submitted = st.form_submit_button(
            "Mulai Registrasi",
            width="stretch",
            type="primary"
        )
        
        if submitted:
            return {
                'name': user_name,
                'shift': shift,
                'role': role
            }
    return None

def render_registration_progress():
    """Render registration progress and instructions"""
    # Progress steps
    steps = [
        "Persiapan Registrasi",
        "Pengambilan Foto Tengah",
        "Pengambilan Foto Kiri",
        "Pengambilan Foto Kanan",
        "Finalisasi"
    ]
    
    current_step = st.session_state.registration_state['current_step']
    
    # Progress bar
    progress_val = current_step / (len(steps) - 1)
    st.progress(progress_val)
    
    # Step indicator
    if current_step < len(steps):
        st.info(f"📸 Langkah saat ini: {steps[current_step]}")
    
    # Instructions based on current step
    if current_step == 0:
        st.info("Tunggu sebentar, window kamera akan terbuka...")
    elif current_step == 1:
        st.info("Posisikan wajah menghadap ke kamera")
    elif current_step == 2:
        st.info("Posisikan wajah menghadap ke kiri")
    elif current_step == 3:
        st.info("Posisikan wajah menghadap ke kanan")
    elif current_step == 4:
        st.success("✅ Registrasi selesai!")
        st.info("Silakan kembali ke User Management untuk melihat hasilnya")
        
        if st.button("Kembali ke User Management", width="stretch"):
            navigate_to("User Management")
            st.rerun()

def show_user_registration():
    """Handle user registration process"""
    st.header("Register New User")
    st.write("Gunakan halaman ini untuk mendaftarkan user baru ke sistem face recognition.")
    
    reg_state = st.session_state.registration_state
    
    # Jika sedang dalam proses registrasi
    if reg_state['is_registering']:
        render_registration_progress()
        
        # Check process status
        is_running, status = get_registration_status(reg_state['process'])
        if not is_running:
            # Process finished
            if status == "Proses selesai":
                reg_state['current_step'] = 4  # Final step
            else:
                reg_state['error'] = status
                reg_state['is_registering'] = False
        
        # Handle error
        if reg_state['error']:
            st.error(f"❌ {reg_state['error']}")
            if st.button("Coba Lagi", width="stretch"):
                st.session_state.registration_state = {
                    'is_registering': False,
                    'current_step': 0,
                    'user_data': None,
                    'process': None,
                    'error': None
                }
                st.rerun()
                
    # Jika belum memulai registrasi
    else:
        user_data = render_registration_form()
        
        if user_data:
            # Validate input
            is_valid, error_msg = validate_user_input(user_data)
            if not is_valid:
                st.error(error_msg)
                return
                
            # Start registration
            success, message, process = prepare_registration(user_data)
            
            if success:
                # Update state
                st.session_state.registration_state = {
                    'is_registering': True,
                    'current_step': 0,
                    'user_data': user_data,
                    'process': process,
                    'error': None
                }
                st.rerun()
            else:
                st.error(message)
                st.error("Pastikan Python dan webcam tersedia")

def show_user_management():
    """Display and manage registered users"""
    st.header("User Management")
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        st.write("Tambah user baru ke sistem")
        if st.button("Tambah User Baru", width="stretch"):
            st.session_state['current_page'] = "Register New User"
            st.rerun()
    
        with col2:
            if st.button("Refresh Daftar User", width="stretch"):
                st.rerun()    # Show user list
    st.subheader("Daftar User Terdaftar")
    attendance_dir = Path(__file__).parent.parent / "Attendance_data"
    
    if not attendance_dir.exists():
        st.warning("Direktori Attendance_data tidak ditemukan")
        return
        
    # Get users
    user_images = list(attendance_dir.glob("*.png"))
    user_folders = [d for d in attendance_dir.iterdir() if d.is_dir()]
    
    if not user_images and not user_folders:
        st.info("Belum ada user terdaftar dalam sistem")
        return
            
    # Display in grid
    cols = st.columns(4)
    col_idx = 0
    
    # Show individual images
    for img_path in user_images:
        user_name = img_path.stem
        with cols[col_idx]:
            st.image(str(img_path), caption=user_name, width="stretch")
            if st.button("Hapus", key=f"del_{user_name}"):
                try:
                    os.remove(img_path)
                    st.success(f"User {user_name} berhasil dihapus")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal menghapus user: {str(e)}")
        col_idx = (col_idx + 1) % 4
    
    # Show folders
    for folder in user_folders:
        user_name = folder.name
        center_img = folder / "center.png"
        
        if center_img.exists():
            with cols[col_idx]:
                st.image(str(center_img), caption=user_name, width="stretch")
                if st.button("Hapus", key=f"del_{user_name}"):
                    try:
                        shutil.rmtree(folder)
                        st.success(f"User {user_name} berhasil dihapus")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menghapus user: {str(e)}")
            col_idx = (col_idx + 1) % 4

def show_user_registration():
    st.header("Register New User")
    st.write("Use this page to register new users for face recognition.")
    
    # Add a form for user registration
    with st.form("user_registration"):
        user_name = st.text_input("Enter User Name").strip()
        submitted = st.form_submit_button("Register User")
        
        if submitted and user_name:
            # Run the initial_data_capture.py script with the user name
            import subprocess
            import os
            
            script_path = os.path.join(os.path.dirname(__file__), "..", "initial_data_capture.py")
            
            try:
                # Start the registration process
                st.info(f"Starting registration process for user: {user_name}")
                
                # Run the script
                result = subprocess.run(
                    ["python", script_path, user_name],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    st.success(f"Successfully registered user: {user_name}")
                else:
                    st.error(f"Error during registration: {result.stderr}")
            except Exception as e:
                st.error(f"Failed to start registration process: {str(e)}")
        elif submitted:
            st.warning("Please enter a user name")

if __name__ == "__main__":
    main()
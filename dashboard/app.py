import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta
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

# Import modules
from registration import show_user_registration, navigate_to
from user_management import show_user_management

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

def export_attendance_to_csv(df, filename):
    """Export attendance data to CSV"""
    try:
        # Create Attendance_Entry directory if not exists
        export_dir = Path(__file__).parent.parent / "Attendance_Entry"
        export_dir.mkdir(exist_ok=True)
        
        # Save to CSV
        export_path = export_dir / filename
        df.to_csv(export_path, index=False)
        return True, export_path
    except Exception as e:
        return False, str(e)

def show_daily_statistics():
    st.header("Daily Statistics")
    
    # Add Export & Import buttons
    col1, col2 = st.columns([1, 1])
    
    def prepare_attendance_data(df):
        """Prepare attendance data by converting date/time columns"""
        try:
            # Convert date column
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            elif 'Date' in df.columns:
                df['date'] = pd.to_datetime(df['Date'])
                df = df.rename(columns={'Date': 'date'})
            
            # Convert time column
            if 'time' in df.columns:
                df['time'] = pd.to_datetime(df['time']).dt.time
            elif 'Time' in df.columns:
                df['time'] = pd.to_datetime(df['Time']).dt.time
                df = df.rename(columns={'Time': 'time'})
            
            return df, None
        except Exception as e:
            return None, str(e)
    
    with col1:
        # Get the data first
        df = get_all_attendance()
        if not df.empty:
            # Prepare data
            prepared_df, error = prepare_attendance_data(df)
            
            if error:
                st.error(f"Error saat memproses data: {error}")
                return
                
            df = prepared_df
            
            # Add weekly filter
            current_date = datetime.now()
            start_of_week = current_date - timedelta(days=current_date.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            
            # Format untuk nama file
            period = st.selectbox(
                "Periode",
                ["Hari Ini", "Minggu Ini", "Bulan Ini", "Semua"],
                help="Pilih periode data yang akan diexport"
            )
            
            if st.button("📥 Download CSV", width="stretch"):
                try:
                    # Filter data berdasarkan periode
                    if period == "Hari Ini":
                        mask = df['date'].dt.date == current_date.date()
                        filename = f"Attendance_{current_date.strftime('%d_%m_%y')}.csv"
                    elif period == "Minggu Ini":
                        mask = (df['date'].dt.date >= start_of_week.date()) & (df['date'].dt.date <= end_of_week.date())
                        filename = f"Weekly_Attendance_{start_of_week.strftime('%d_%m_%y')}_to_{end_of_week.strftime('%d_%m_%y')}.csv"
                    elif period == "Bulan Ini":
                        mask = df['date'].dt.to_period('M') == current_date.to_period('M')
                        filename = f"Monthly_Attendance_{current_date.strftime('%m_%Y')}.csv"
                    else:  # Semua
                        mask = pd.Series(True, index=df.index)
                        filename = f"All_Attendance_as_of_{current_date.strftime('%d_%m_%y')}.csv"
                    
                    # Filter dan persiapkan data untuk download
                    filtered_df = df[mask].copy()
                    
                    if not filtered_df.empty:
                        # Convert datetime to string untuk CSV
                        if 'date' in filtered_df.columns:
                            filtered_df['date'] = filtered_df['date'].dt.strftime('%Y-%m-%d')
                        if 'time' in filtered_df.columns:
                            filtered_df['time'] = filtered_df['time'].astype(str)
                        
                        # Download CSV
                        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            "💾 Simpan File",
                            csv_data,
                            filename,
                            "text/csv",
                            key='save-csv'
                        )
                        st.success(f"✅ File siap didownload: {filename}")
                    else:
                        st.warning(f"⚠️ Tidak ada data untuk periode {period.lower()}")
                        
                except Exception as e:
                    st.error(f"❌ Error saat memproses data: {str(e)}")
                    st.info("Silakan coba lagi atau pilih periode yang berbeda")
                
                filtered_df = df[mask]
                
                if not filtered_df.empty:
                    csv = filtered_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "💾 Simpan CSV",
                        csv,
                        filename,
                        "text/csv",
                        key='download-csv'
                    )
                    st.success(f"✅ Data siap didownload: {filename}")
                else:
                    st.warning(f"⚠️ Tidak ada data untuk periode {period.lower()}")
        else:
            st.warning("⚠️ Tidak ada data untuk di-export")
    
    with col2:
        uploaded_file = st.file_uploader(
            "📥 Import CSV",
            type=['csv'],
            help="Upload file CSV untuk import data absensi"
        )
        
        if uploaded_file is not None:
            try:
                # Read CSV
                import_df = pd.read_csv(uploaded_file)
                
                # Validate columns
                required_cols = ['employee_name', 'date', 'time', 'status']
                missing_cols = [col for col in required_cols if col not in import_df.columns]
                
                if missing_cols:
                    st.error(f"❌ Kolom yang diperlukan tidak ditemukan: {', '.join(missing_cols)}")
                    st.info("""
                    Format CSV yang diperlukan:
                    - employee_name: Nama karyawan
                    - date: Tanggal (YYYY-MM-DD)
                    - time: Waktu (HH:MM:SS)
                    - status: Status (on_time/late)
                    """)
                    return
                
                # Show preview
                st.subheader("Preview Data Import")
                st.dataframe(import_df.head())
                
                # Confirm import
                if st.button("✅ Konfirmasi Import", width="stretch"):
                    # Save to attendance directory
                    filename = f"Attendance_{datetime.now().strftime('%d_%m_%y')}.csv"
                    success, result = export_attendance_to_csv(import_df, filename)
                    
                    if success:
                        st.success("✅ Data berhasil diimport!")
                        st.rerun()  # Refresh page to show new data
                    else:
                        st.error(f"❌ Gagal import data: {result}")
                        
            except Exception as e:
                st.error(f"❌ Error saat membaca file: {str(e)}")
                st.info("Pastikan format file CSV sesuai")
    
    # Show statistics
    st.markdown("---")
    st.subheader("Statistik Kehadiran")
    
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
        
        # Daily attendance chart
        daily_counts = df.groupby(date_column).size().reset_index(name='count')
        fig = px.line(
            daily_counts,
            x=date_column,
            y='count',
            title='Tren Kehadiran Harian'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Hourly distribution
        if time_column in df.columns:
            df['Hour'] = pd.to_datetime(df[time_column]).dt.hour
            hourly_counts = df.groupby('Hour').size().reset_index(name='count')
            
            fig2 = px.bar(
                hourly_counts,
                x='Hour',
                y='count',
                title='Distribusi Jam Kehadiran'
            )
            st.plotly_chart(fig2, use_container_width=True)
            
        # Status distribution if available
        if 'status' in df.columns:
            status_counts = df['status'].value_counts()
            fig3 = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title='Distribusi Status Kehadiran'
            )
            st.plotly_chart(fig3, use_container_width=True)
            
        # Show weekly summary
        st.subheader("Rekap Mingguan")
        
        # Get current week dates
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        dates_of_week = [(start_of_week + timedelta(days=x)).date() for x in range(7)]
        
        # Create weekly summary
        weekly_data = []
        for date in dates_of_week:
            day_data = df[df[date_column].dt.date == date]
            
            # Calculate statistics
            total_attendance = len(day_data)
            on_time = len(day_data[day_data['status'] == 'on_time']) if 'status' in day_data.columns else 0
            late = len(day_data[day_data['status'] == 'late']) if 'status' in day_data.columns else 0
            
            weekly_data.append({
                'Tanggal': date.strftime('%d %b %Y'),
                'Hari': ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu'][date.weekday()],
                'Total Hadir': total_attendance,
                'Tepat Waktu': on_time,
                'Terlambat': late
            })
        
        # Display weekly summary
        weekly_df = pd.DataFrame(weekly_data)
        st.dataframe(
            weekly_df,
            column_config={
                'Tanggal': st.column_config.TextColumn('Tanggal', width='medium'),
                'Hari': st.column_config.TextColumn('Hari', width='small'),
                'Total Hadir': st.column_config.NumberColumn('Total Hadir', format='%d'),
                'Tepat Waktu': st.column_config.NumberColumn('Tepat Waktu', format='%d'),
                'Terlambat': st.column_config.NumberColumn('Terlambat', format='%d')
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Show detailed data in expander
        with st.expander("Lihat Detail Data"):
            # Filter options
            filter_type = st.selectbox(
                "Filter Berdasarkan",
                ["Hari Ini", "Minggu Ini", "Pilih Tanggal"]
            )
            
            if filter_type == "Hari Ini":
                filtered_df = df[df[date_column].dt.date == today.date()]
            elif filter_type == "Minggu Ini":
                filtered_df = df[
                    (df[date_column].dt.date >= start_of_week.date()) & 
                    (df[date_column].dt.date <= (start_of_week + timedelta(days=6)).date())
                ]
            else:  # Pilih Tanggal
                selected_date = st.date_input("Pilih Tanggal")
                filtered_df = df[df[date_column].dt.date == selected_date]
            
            if not filtered_df.empty:
                st.dataframe(
                    filtered_df.sort_values(by=date_column, ascending=False),
                    use_container_width=True
                )
                
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Kehadiran", len(filtered_df))
                with col2:
                    on_time = len(filtered_df[filtered_df['status'] == 'on_time']) if 'status' in filtered_df.columns else 0
                    st.metric("Tepat Waktu", on_time)
                with col3:
                    late = len(filtered_df[filtered_df['status'] == 'late']) if 'status' in filtered_df.columns else 0
                    st.metric("Terlambat", late)
            else:
                st.info("Tidak ada data untuk periode yang dipilih")
    else:
        st.info("Belum ada data absensi tersedia")

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
            padding: 1rem;
            text-align: center;
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
            return False, f"❌ Script registrasi tidak ditemukan di: {script_path}", None
            
        # Cek user exists
        if check_user_exists(user_data['name']):
            return False, f"❌ User dengan nama '{user_data['name']}' sudah terdaftar!", None
            
        # Siapkan command dengan pipe agar bisa capture output
        process = subprocess.Popen(
            [sys.executable, str(script_path), user_data['name']],
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True)
            
        # Tunggu sebentar untuk memastikan process mulai
        time.sleep(1)
        
        if process.poll() is not None:  # Process gagal dimulai
            return False, "❌ Gagal memulai proses registrasi", None
            
        return True, "✅ Proses registrasi dimulai!", process
        
    except Exception as e:
        return False, f"❌ Error: {str(e)}", None

def get_registration_status(process: subprocess.Popen) -> tuple[bool, str]:
    """
    Check registration process status from running process
    Returns: (is_running, status_message)
    """
    if not process:
        return False, "❌ Process tidak ditemukan"
        
    # Cek apakah process masih berjalan
    if process.poll() is None:
        # Coba baca output terakhir
        try:
            # Baca output tanpa blocking
            stdout = process.stdout.readline().strip()
            stderr = process.stderr.readline().strip()
            
            # Update status based on output
            if stdout:
                if "center image captured" in stdout.lower():
                    return True, "✅ Foto tengah berhasil diambil"
                elif "left image captured" in stdout.lower():
                    return True, "✅ Foto kiri berhasil diambil"
                elif "right image captured" in stdout.lower():
                    return True, "✅ Foto kanan berhasil diambil"
                elif "Look at CENTER" in stdout:
                    return True, "🎯 Lihat ke tengah"
                elif "TURN LEFT" in stdout:
                    return True, "👈 Hadap ke kiri"
                elif "TURN RIGHT" in stdout:
                    return True, "👉 Hadap ke kanan"
                elif "Get ready" in stdout:
                    return True, "⏳ Bersiap untuk foto..."
                elif "All images captured" in stdout:
                    return False, "✅ Registrasi berhasil!"
                else:
                    return True, stdout
            
            # Cek error
            if stderr:
                return False, f"❌ Error: {stderr}"
                
            # Process masih jalan tapi tidak ada output baru
            return True, "⏳ Memproses..."
            
        except Exception as e:
            # Masih jalan tapi tidak bisa baca output
            return True, "⏳ Memproses..."
            




if __name__ == "__main__":
    main()
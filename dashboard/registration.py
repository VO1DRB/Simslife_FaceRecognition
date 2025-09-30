import streamlit as st
from pathlib import Path
import subprocess
import time
import sys
import os

def navigate_to(page_name: str):
    """
    Navigate to a different page and reset registration state if needed
    """
    st.session_state['current_page'] = page_name
    if page_name != 'Register New User':
        st.session_state['registration_state'] = {
            'is_registering': False,
            'current_step': 0,
            'user_data': None,
            'process': None,
            'error': None
        }

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
            
    else:
        # Process selesai
        if process.returncode == 0:
            return False, "✅ Registrasi selesai"
        else:
            stderr = process.stderr.read()
            return False, f"❌ Error: {stderr if stderr else 'Unknown error'}"

def render_registration_form() -> dict:
    """
    Render the registration form and return user input
    """
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
    """
    Render registration progress and instructions
    """
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
    """
    Handle user registration process
    """
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
            if not user_data['name']:
                st.error("❌ Nama user harus diisi!")
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
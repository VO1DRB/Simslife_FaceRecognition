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
    # Get the root project directory (where main.py is)
    root_dir = Path(__file__).parent.parent
    attendance_dir = root_dir / "Attendance_data"
    
    # Check both single image and folder formats
    user_file = attendance_dir / f"{name}.png"
    user_folder = attendance_dir / name
    
    # Also check if user exists in either location
    dashboard_attendance_dir = Path(__file__).parent / "Attendance_data"
    dashboard_user_file = dashboard_attendance_dir / f"{name}.png"
    dashboard_user_folder = dashboard_attendance_dir / name
    
    return any([
        user_file.exists(),
        user_folder.exists(),
        dashboard_user_file.exists(),
        dashboard_user_folder.exists()
    ])

def prepare_registration(user_data: dict) -> tuple[bool, str, None]:
    """
    Prepare the registration process (integrated version)
    Returns: (success, message, None)
    """
    try:
        # Get root project directory
        root_dir = Path(__file__).parent.parent.resolve()
        
        # Save user data for shift management
        user_data_file = root_dir / "user_data.json"
        try:
            import json
            if user_data_file.exists():
                with open(user_data_file, 'r') as f:
                    saved_data = json.load(f)
            else:
                saved_data = {}
            
            # Add new user data
            saved_data[user_data['name']] = {
                'shift': user_data['shift'],
                'role': user_data['role']
            }
            
            with open(user_data_file, 'w') as f:
                json.dump(saved_data, f, indent=4)
        except Exception as e:
            st.warning(f"Warning: Could not save user shift data: {str(e)}")
        
        # Cek user exists
        if check_user_exists(user_data['name']):
            return False, f"❌ User dengan nama '{user_data['name']}' sudah terdaftar!", None
            
        # Make sure main Attendance_data directory exists
        attendance_dir = root_dir / "Attendance_data"
        attendance_dir.mkdir(exist_ok=True)
        
        # Create user directory
        user_dir = attendance_dir / user_data['name']
        user_dir.mkdir(exist_ok=True)
        
        # Initialize registration state
        return True, "✅ Proses registrasi dimulai! Silakan ikuti instruksi selanjutnya.", None
        
    except Exception as e:
        return False, f"❌ Error: {str(e)}", None

def check_registration_complete() -> tuple[bool, str]:
    """
    Check if registration is complete by verifying all required images exist
    Returns: (is_complete, status_message)
    """
    if 'registration_state' not in st.session_state or not st.session_state.registration_state['user_data']:
        return False, "❌ No active registration"
    
    username = st.session_state.registration_state['user_data']['name']
    root_dir = Path(__file__).parent.parent
    user_folder = root_dir / "Attendance_data" / username
    
    # Check if all required images exist
    if user_folder.exists():
        missing_poses = []
        for pose in ['center', 'left', 'right']:
            if not (user_folder / f"{pose}.png").exists():
                missing_poses.append(pose)
        
        if not missing_poses:
            return True, "✅ Registrasi berhasil!"
        else:
            return False, f"⏳ Masih perlu foto: {', '.join(missing_poses)}"
    else:
        return False, "⏳ Persiapan registrasi..."

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
        st.success("✅ Registrasi selesai! Form akan direset otomatis...")

def show_user_registration():
    """
    Handle user registration process
    """
    # Import all necessary functions from utils package
    from utils import get_camera_feed, capture_and_save_face, get_orientation_instructions
    
    st.header("Register New User")
    st.write("Gunakan halaman ini untuk mendaftarkan user baru ke sistem face recognition.")
    
    reg_state = st.session_state.registration_state
    
    # Jika sedang dalam proses registrasi
    if reg_state['is_registering']:
        # Show registration instructions
        render_registration_progress()
        
        # Create columns for layout
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Get camera feed
            camera_image = get_camera_feed()
            
            # Show capture button based on current step
            current_step = reg_state['current_step']
            if camera_image is not None:
                # Convert the image from bytes to OpenCV format
                import cv2
                import numpy as np
                
                bytes_data = camera_image.getvalue()
                img_array = np.frombuffer(bytes_data, np.uint8)
                image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                
                # Determine pose based on current step
                poses = ['center', 'left', 'right']
                if current_step > 0 and current_step <= len(poses):
                    pose = poses[current_step - 1]
                    
                    # Button to capture the current pose
                    if st.button(f"Capture {pose.title()} Image", key=f"capture_{pose}"):
                        # Get user folder path
                        root_dir = Path(__file__).parent.parent
                        user_folder = root_dir / "Attendance_data" / reg_state['user_data']['name']
                        
                        # Save captured image
                        success = capture_and_save_face(image, user_folder, pose)
                        
                        if success:
                            st.success(f"✅ {pose.title()} image captured successfully!")
                            # Move to next step
                            reg_state['current_step'] += 1
                            
                            # Check if registration is complete
                            is_complete, _ = check_registration_complete()
                            if is_complete:
                                reg_state['current_step'] = 4  # Final step
                                st.rerun()
                            elif reg_state['current_step'] > 3:
                                reg_state['current_step'] = 4  # Final step
                                st.rerun()
                        else:
                            st.error(f"❌ Failed to capture {pose} image. Please try again.")
        
        with col2:
            st.subheader("Instructions")
            
            # Display instructions based on current step
            instruction = get_orientation_instructions(reg_state['current_step'] - 1)
            st.info(instruction)
            
            # Option to cancel registration
            if st.button("Cancel Registration", type="secondary"):
                # Reset registration state
                st.session_state.registration_state = {
                    'is_registering': False,
                    'current_step': 0,
                    'user_data': None,
                    'process': None,
                    'error': None
                }
                st.rerun()
        
        # Check if registration is complete (all images captured)
        if reg_state['current_step'] == 4:
            is_complete, status = check_registration_complete()
            if is_complete:
                st.success(status)
                # Reset form for next registration after delay
                import time
                time.sleep(1)  # Show success message briefly
                st.session_state.registration_state = {
                    'is_registering': False,
                    'current_step': 0,
                    'user_data': None,
                    'process': None,
                    'error': None
                }
                st.rerun()
            else:
                st.warning("Registration incomplete. Please capture all required images.")
                # Reset to step 1 to start captures again
                reg_state['current_step'] = 1
                st.rerun()
                
    # Jika belum memulai registrasi
    else:
        user_data = render_registration_form()
        
        if user_data:
            if not user_data['name']:
                st.error("❌ Nama user harus diisi!")
                return
                
            # Start registration
            success, message, _ = prepare_registration(user_data)
            
            if success:
                # Update state
                st.session_state.registration_state = {
                    'is_registering': True,
                    'current_step': 1,  # Start with center capture
                    'user_data': user_data,
                    'process': None,
                    'error': None
                }
                st.rerun()
            else:
                st.error(message)
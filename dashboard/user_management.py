from pathlib import Path
import streamlit as st
import shutil
import os
import time

def show_user_management():
    """
    Display and manage registered users
    """
    st.header("User Management")
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        st.write("Tambah user baru ke sistem")
        if st.button("➕ Tambah User Baru", type="primary", width="stretch"):
            st.session_state['current_page'] = "Register New User"
            st.rerun()
    
    with col2:
        if st.button("🔄 Refresh Daftar User", width="stretch"):
            st.rerun()
    
    st.subheader("Daftar User Terdaftar")
    attendance_dir = Path(__file__).parent.parent / "Attendance_data"
    
    if not attendance_dir.exists():
        st.warning("⚠️ Direktori Attendance_data tidak ditemukan")
        return
        
    # Get users
    user_images = list(attendance_dir.glob("*.png"))
    user_folders = [d for d in attendance_dir.iterdir() if d.is_dir()]
    
    if not user_images and not user_folders:
        st.info("ℹ️ Belum ada user terdaftar dalam sistem")
        return
            
    # Display in grid
    cols = st.columns(4)
    col_idx = 0
    
    # Show individual images
    for img_path in user_images:
        user_name = img_path.stem
        with cols[col_idx]:
            st.image(str(img_path), caption=user_name, width="stretch")
            if st.button("🗑️ Hapus User", key=f"del_btn_{user_name}", type="secondary"):
                st.warning(f"⚠️ Yakin ingin menghapus user '{user_name}'?")
                confirm_col1, confirm_col2 = st.columns(2)
                with confirm_col1:
                    if st.button("✅ Ya, Hapus", key=f"confirm_{user_name}", type="primary"):
                        try:
                            # Delete from Attendance_data
                            os.remove(img_path)
                            # Also delete from user_data.json if exists
                            user_data_file = attendance_dir.parent / "user_data.json"
                            if user_data_file.exists():
                                import json
                                try:
                                    with open(user_data_file, 'r') as f:
                                        data = json.load(f)
                                    if user_name in data:
                                        del data[user_name]
                                        with open(user_data_file, 'w') as f:
                                            json.dump(data, f, indent=4)
                                except:
                                    pass  # Ignore user_data.json errors
                            st.success(f"✅ User {user_name} berhasil dihapus")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Gagal menghapus user: {str(e)}")
                with confirm_col2:
                    if st.button("❌ Batal", key=f"cancel_{user_name}"):
                        st.rerun()
        col_idx = (col_idx + 1) % 4
    
    # Show folders
    for folder in user_folders:
        user_name = folder.name
        center_img = folder / "center.png"
        
        if center_img.exists():
            with cols[col_idx]:
                st.image(str(center_img), caption=user_name, width="stretch")
                
                # Add delete confirmation
                if st.button("🗑️ Hapus User", key=f"del_btn_{user_name}", type="secondary"):
                    st.warning(f"⚠️ Yakin ingin menghapus user '{user_name}'?")
                    confirm_col1, confirm_col2 = st.columns(2)
                    with confirm_col1:
                        if st.button("✅ Ya, Hapus", key=f"confirm_{user_name}", type="primary"):
                            try:
                                # Delete user folder
                                shutil.rmtree(folder)
                                
                                # Also delete from user_data.json if exists
                                user_data_file = attendance_dir.parent / "user_data.json"
                                if user_data_file.exists():
                                    import json
                                    try:
                                        with open(user_data_file, 'r') as f:
                                            data = json.load(f)
                                        if user_name in data:
                                            del data[user_name]
                                            with open(user_data_file, 'w') as f:
                                                json.dump(data, f, indent=4)
                                    except:
                                        pass  # Ignore user_data.json errors
                                
                                st.success(f"✅ User {user_name} berhasil dihapus")
                                time.sleep(1)  # Give time to read message
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Gagal menghapus user: {str(e)}")
                    with confirm_col2:
                        if st.button("❌ Batal", key=f"cancel_{user_name}"):
                            st.rerun()
            col_idx = (col_idx + 1) % 4
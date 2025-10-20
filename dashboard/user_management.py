import streamlit as st
import os
import shutil
import json
from pathlib import Path
import requests

API_URL = "http://localhost:8000"

def api_call(endpoint: str, method="get", **kwargs):
    """Helper untuk panggil API"""
    url = f"{API_URL}{endpoint}"
    try:
        if method == "get":
            r = requests.get(url, **kwargs)
        elif method == "delete":
            r = requests.delete(url, **kwargs)
        elif method == "post":
            r = requests.post(url, **kwargs)
        else:
            raise ValueError("Method tidak dikenal")

        if r.status_code != 200:
            st.error(f"API Error {r.status_code}: {r.text}")
            return None
        return r.json()
    except Exception as e:
        st.error(f"Gagal koneksi ke API: {e}")
        return None


def show_user_management():
    st.header("👤 User Management")

    attendance_dir = Path(__file__).parent.parent / "Attendance_data"
    if not attendance_dir.exists():
        st.warning("⚠️ Folder Attendance_data tidak ditemukan.")
        return

    # Ambil semua user (file dan folder)
    user_images = list(attendance_dir.glob("*.png"))
    user_folders = [d for d in attendance_dir.iterdir() if d.is_dir()]

    if not user_images and not user_folders:
        st.info("Belum ada user.")
        return

    st.subheader("Single Image Users")
    _render_user_section(user_images, attendance_dir)

    st.subheader("Multiple Image Users")
    _render_user_section(user_folders, attendance_dir)


def _render_user_section(items, base_dir):
    cols = st.columns(4)
    for i, item in enumerate(items):
        with cols[i % 4]:
            # Tentukan nama user dan thumbnail
            user_name = item.stem if item.suffix == ".png" else item.name
            img_path = item if item.suffix == ".png" else item / "center.png"

            if img_path.exists():
                st.image(str(img_path), caption=user_name, use_container_width=True)
            else:
                st.write(f"📁 {user_name}")

            # Tombol aksi
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Hapus", key=f"del_{user_name}"):
                    _delete_user(user_name, base_dir)
            with col2:
                if st.button("✏️ Edit", key=f"edit_{user_name}"):
                    _edit_user(user_name)


def _delete_user(user_name: str, base_dir: Path):
    """Hapus user baik berupa file single image maupun folder multiple image"""
    st.warning(f"⚠️ Konfirmasi hapus data user: **{user_name}**")
    if st.button(f"✅ Ya, hapus {user_name}", key=f"confirm_delete_{user_name}"):
        try:
            # Import fungsi delete_user_completely dari utils.user_data
            from utils.user_data import delete_user_completely
            
            # Gunakan fungsi yang lebih lengkap untuk menghapus user sepenuhnya
            success, message = delete_user_completely(user_name)
            
            if success:
                st.success(f"✅ User '{user_name}' berhasil dihapus.")
            else:
                st.error(f"⚠️ Terjadi masalah saat menghapus: {message}")
                
            # Tetap rerun untuk menyegarkan UI
            st.rerun()
        except Exception as e:
            st.error(f"Gagal menghapus {user_name}: {e}")


def _remove_from_json(base_dir: Path, user_name: str):
    """Hapus entri user di user_data.json"""
    json_path = base_dir.parent / "user_data.json"
    if not json_path.exists():
        return
    try:
        with open(json_path, "r") as f:
            data = json.load(f)
        if user_name in data:
            del data[user_name]
            with open(json_path, "w") as f:
                json.dump(data, f, indent=4)
    except Exception as e:
        st.error(f"Gagal update user_data.json: {e}")


def _edit_user(user_name: str):
    """Edit nama dan role user"""
    st.subheader(f"✏️ Edit Data User: {user_name}")

    json_path = Path(__file__).parent.parent / "user_data.json"
    data = {}
    if json_path.exists():
        with open(json_path, "r") as f:
            data = json.load(f)

    current_role = data.get(user_name, {}).get("role", "")
    new_name = st.text_input("Nama User", value=user_name)
    new_role = st.text_input("Role", value=current_role)

    if st.button("💾 Simpan"):
        try:
            # Rename folder/file sesuai nama baru
            attendance_dir = Path(__file__).parent.parent / "Attendance_data"
            old_folder = attendance_dir / user_name
            new_folder = attendance_dir / new_name
            old_file = attendance_dir / f"{user_name}.png"
            new_file = attendance_dir / f"{new_name}.png"

            if old_folder.exists() and old_folder.is_dir():
                old_folder.rename(new_folder)
            if old_file.exists():
                old_file.rename(new_file)

            # Update user_data.json
            if user_name in data:
                del data[user_name]
            data[new_name] = {"role": new_role}
            with open(json_path, "w") as f:
                json.dump(data, f, indent=4)

            st.success(f"✅ Data user '{user_name}' berhasil diperbarui jadi '{new_name}'")
            st.rerun()
        except Exception as e:
            st.error(f"Gagal update data user: {e}")

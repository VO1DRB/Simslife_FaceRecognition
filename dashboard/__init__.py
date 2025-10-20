"""
Dashboard application for Face Recognition Attendance System
"""
import os
import subprocess
import sys
import pkg_resources

# Required packages for the dashboard
required_packages = [
    'streamlit',
    'pandas',
    'plotly',
    'opencv-python',
    'face_recognition',
    'numpy',
    'pygame',
    'requests',
    'psutil'
]

def check_and_install_packages():
    """Check and install required packages"""
    installed_packages = {pkg.key for pkg in pkg_resources.working_set}
    missing_packages = [pkg for pkg in required_packages if pkg.replace('-', '_') not in installed_packages]
    
    if missing_packages:
        print(f"Installing missing packages: {', '.join(missing_packages)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])
        return True
    return False

# Check and install packages at import time
check_and_install_packages()
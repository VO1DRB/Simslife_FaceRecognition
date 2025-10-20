"""
Face recognition utilities initialization file.
Makes importing from the face_recognition_utils module easier.
"""

from .core import (
    # Camera management functions
    start_camera, 
    stop_camera, 
    get_continuous_camera_feed,
    get_camera_feed,
    
    # Face analysis functions
    analyze_face_for_attendance,
    analyze_face_image,
    detect_face_orientation,
    calculate_eye_aspect_ratio,
    
    # Face encoding and data management
    load_face_encodings,
    capture_and_save_face,
    
    # Attendance state management
    initialize_attendance_state,
    reset_attendance_state,
    record_attendance
)

# Import additional utilities
from .orientation import get_orientation_instructions
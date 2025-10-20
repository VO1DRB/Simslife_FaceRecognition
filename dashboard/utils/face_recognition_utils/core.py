import cv2
import numpy as np
import os
import face_recognition
import time
from pathlib import Path
import threading
import queue
from datetime import datetime

# Global variables for video processing
frame_queue = queue.Queue(maxsize=1)
analysis_queue = queue.Queue(maxsize=1)
camera_running = False
camera_thread = None

def initialize_attendance_state():
    """Initialize attendance state if not already present in session state"""
    import streamlit as st
    
    if 'attendance_state' not in st.session_state:
        st.session_state.attendance_state = {
            'last_detection_time': 0,
            'last_detected_name': None,
            'detection_cooldown': 5,  # Seconds
            'recognized_users': [],
            'camera_active': False,
            'is_active': False,
            'recognition_time': None,
            'status_message': None,
            'cooldown': False
        }
    
    return st.session_state.attendance_state

def reset_attendance_state():
    """Reset attendance state in session state"""
    import streamlit as st
    
    if 'attendance_state' in st.session_state:
        st.session_state.attendance_state = {
            'last_detection_time': 0,
            'last_detected_name': None,
            'detection_cooldown': 5,  # Seconds
            'recognized_users': [],
            'camera_active': False,
            'is_active': False,
            'recognition_time': None,
            'status_message': None,
            'cooldown': False
        }
    
    # Stop camera if running
    stop_camera()

def start_camera():
    """Start the camera thread"""
    global camera_running, camera_thread
    
    # Don't start if already running
    if camera_running:
        return True
    
    # Clear queues
    while not frame_queue.empty():
        try:
            frame_queue.get_nowait()
        except queue.Empty:
            pass
            
    while not analysis_queue.empty():
        try:
            analysis_queue.get_nowait()
        except queue.Empty:
            pass
    
    camera_running = True
    camera_thread = threading.Thread(target=camera_worker)
    camera_thread.daemon = True
    camera_thread.start()
    return True

def stop_camera():
    """Stop the camera thread"""
    global camera_running, camera_thread
    
    if camera_running:
        camera_running = False
        if camera_thread:
            camera_thread.join(timeout=1.0)
            camera_thread = None
    
    # Clear queues
    while not frame_queue.empty():
        try:
            frame_queue.get_nowait()
        except queue.Empty:
            pass
            
    while not analysis_queue.empty():
        try:
            analysis_queue.get_nowait()
        except queue.Empty:
            pass

def camera_worker():
    """Worker thread that captures frames from the camera"""
    global camera_running, frame_queue
    import streamlit as st
    
    # Initialize camera
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        st.error("Failed to open camera")
        camera_running = False
        return
    
    # Set camera properties for better performance
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    try:
        while camera_running:
            success, frame = camera.read()
            if not success:
                time.sleep(0.1)
                continue
                
            # Add to queue, replacing old frame if queue is full
            if frame_queue.full():
                try:
                    frame_queue.get_nowait()
                except queue.Empty:
                    pass
            
            try:
                frame_queue.put(frame, block=False)
            except queue.Full:
                pass
                
            time.sleep(0.03)  # ~30 FPS
    finally:
        camera.release()

def get_continuous_camera_feed():
    """
    Get the camera feed for continuous processing
    Returns the latest frame from the camera
    """
    if not camera_running:
        start_camera()
    
    try:
        # Get the latest frame
        frame = frame_queue.get(block=True, timeout=1.0)
        return frame
    except (queue.Empty, Exception) as e:
        return None

def load_face_encodings():
    """
    Load known face encodings and names
    Returns: (known_face_encodings, known_face_names)
    """
    known_face_encodings = []
    known_face_names = []
    
    # Get the root directory
    root_dir = Path(__file__).parent.parent.parent.parent
    attendance_dir = root_dir / "Attendance_data"
    
    # Check if attendance directory exists
    if not attendance_dir.exists():
        return known_face_encodings, known_face_names
    
    # Get list of person folders and files
    items = [f for f in os.listdir(attendance_dir)]
    
    for item in items:
        item_path = attendance_dir / item
        
        # If it's a direct image file
        if item_path.is_file() and item.endswith(('.png', '.jpg', '.jpeg')):
            try:
                # Load image and compute encoding
                image = face_recognition.load_image_file(item_path)
                encodings = face_recognition.face_encodings(image)
                if len(encodings) > 0:
                    encoding = encodings[0]
                    
                    # Add to lists
                    known_face_encodings.append(encoding)
                    known_face_names.append(item.split('.')[0])
            except Exception as e:
                print(f"Error processing {item}: {e}")
                pass
                
        # If it's a directory (multiple angles)
        elif item_path.is_dir():
            # Get center image if available
            center_image_path = item_path / "center.png"
            if center_image_path.exists():
                try:
                    # Load image and compute encoding
                    image = face_recognition.load_image_file(center_image_path)
                    encodings = face_recognition.face_encodings(image)
                    if len(encodings) > 0:
                        encoding = encodings[0]
                        
                        # Add to lists
                        known_face_encodings.append(encoding)
                        known_face_names.append(item)
                except Exception as e:
                    print(f"Error processing {item}/center.png: {e}")
                    pass
    
    return known_face_encodings, known_face_names

def analyze_face_for_attendance(image, known_face_encodings=None, known_face_names=None):
    """
    Analyze face in the image for attendance purposes
    Returns a dict with analysis results
    """
    if image is None:
        return {
            'face_detected': False,
            'name': None,
            'display_image': None,
            'multiple_faces': False
        }
        
    result = {
        'face_detected': False,
        'name': None,
        'display_image': image.copy(),
        'multiple_faces': False,
        'confidence': 0
    }
    
    # Convert BGR image to RGB (for face_recognition)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Detect faces
    face_locations = face_recognition.face_locations(rgb_image)
    
    # Check if multiple faces detected
    if len(face_locations) > 1:
        result['multiple_faces'] = True
    
    if not face_locations or not known_face_encodings or len(known_face_encodings) == 0:
        return result
    
    # Get face encodings for detected faces
    face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
    
    if not face_encodings:
        return result
    
    # Loop through each face found in the frame
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        # Compare with known faces
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)
        
        name = "Unknown"
        confidence = 0
        
        # Use the known face with the smallest distance to the new face
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        if len(face_distances) > 0:
            best_match_index = np.argmin(face_distances)
            confidence = 1 - face_distances[best_match_index]
            
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
        
        # Draw a rectangle around the face
        color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
        cv2.rectangle(result['display_image'], (left, top), (right, bottom), color, 2)

        # Draw a label with a name below the face
        cv2.rectangle(result['display_image'], (left, bottom - 35), (right, bottom), color, cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        
        # Display name and confidence
        text = f"{name} ({confidence:.2f})"
        cv2.putText(result['display_image'], text, (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)
        
        # Update result
        result['face_detected'] = True
        result['name'] = name
        result['confidence'] = confidence
        
        # Only process the first face for attendance
        break
    
    return result

def record_attendance(name):
    """
    Record attendance for the recognized person
    Returns: True if recorded successfully
    """
    if not name or name == "Unknown":
        return False
    
    try:
        # Get current time
        now = datetime.now()
        current_date = now.strftime("%y_%m_%d")
        current_time = now.strftime("%H:%M:%S")
        
        # Get attendance file path
        root_dir = Path(__file__).parent.parent.parent.parent
        attendance_dir = root_dir / "Attendance_Entry"
        attendance_dir.mkdir(exist_ok=True)
        
        attendance_file = attendance_dir / f"Attendance_{current_date}.csv"
        
        # Check if file exists, if not create with header
        if not attendance_file.exists():
            with open(attendance_file, 'w', newline='') as f:
                f.write("Name,Time,Date,Status\n")
        
        # Get current records to check if already attended
        with open(attendance_file, 'r') as f:
            records = f.readlines()
            
        # Check if already attended
        name_records = [r for r in records if r.startswith(f"{name},")]
        
        # If already checked in, record as check-out
        status = "Check-In"
        if name_records and len(name_records) % 2 == 1:  # Odd number of records -> already checked in
            status = "Check-Out"
        
        # Append to file
        with open(attendance_file, 'a', newline='') as f:
            f.write(f"{name},{current_time},{now.strftime('%d/%m/%Y')},{status}\n")
        
        return True
    except Exception as e:
        print(f"Error recording attendance: {e}")
        return False

def get_camera_feed():
    """
    Creates a Streamlit camera component that can be used in the dashboard.
    This function returns a camera object that can be used to get frames.
    """
    import streamlit as st
    
    # Use st.camera_input to capture from webcam directly in the browser
    camera_image = st.camera_input("Camera", key="camera_feed")
    
    return camera_image

def analyze_face_image(image, known_face_encodings=None, known_face_names=None):
    """
    Analyzes a face in an image and compares it with known faces.
    
    Args:
        image: The image captured from the camera
        known_face_encodings: List of known face encodings
        known_face_names: List of names corresponding to the encodings
    
    Returns:
        Dict with detection results including face locations, names, etc.
    """
    if image is None:
        return None
    
    # Convert the image from BGR to RGB format
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Resize for faster face recognition processing
    small_frame = cv2.resize(image_rgb, (0, 0), fx=0.25, fy=0.25)
    
    # Find all faces in the current frame
    face_locations = face_recognition.face_locations(small_frame)
    
    result = {
        "face_detected": len(face_locations) > 0,
        "multiple_faces": len(face_locations) > 1,
        "face_locations": face_locations,
        "recognized_name": None,
        "match_confidence": None,
        "face_encoding": None
    }
    
    # If faces are found and we have reference encodings, try to identify them
    if face_locations and known_face_encodings is not None and known_face_names is not None:
        face_encodings = face_recognition.face_encodings(small_frame, face_locations)
        
        if face_encodings:
            result["face_encoding"] = face_encodings[0]
            
            # Compare the detected face with our known faces
            face_distances = face_recognition.face_distance(known_face_encodings, face_encodings[0])
            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                match_confidence = 1 - face_distances[best_match_index]
                
                # If the face is a close match
                if match_confidence > 0.6:  # Threshold for recognition
                    result["recognized_name"] = known_face_names[best_match_index]
                    result["match_confidence"] = match_confidence
    
    return result

def capture_and_save_face(image, output_path, pose="center"):
    """
    Captures an image of a face and saves it to the specified path.
    
    Args:
        image: Image from which to extract the face
        output_path: Directory path where to save the image
        pose: The pose name (center, left, right)
    
    Returns:
        bool: True if successful, False otherwise
    """
    if image is None:
        return False
        
    try:
        # Create directory if it doesn't exist
        os.makedirs(output_path, exist_ok=True)
        
        # Convert to RGB (face_recognition uses RGB)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        face_locations = face_recognition.face_locations(rgb_image)
        
        if not face_locations:
            return False
            
        # Take the first face found
        top, right, bottom, left = face_locations[0]
        
        # Add margin around face (20% of face size)
        height = bottom - top
        width = right - left
        margin_h = int(height * 0.2)
        margin_w = int(width * 0.2)
        
        # Ensure we don't go outside image bounds
        h, w = image.shape[:2]
        top = max(0, top - margin_h)
        bottom = min(h, bottom + margin_h)
        left = max(0, left - margin_w)
        right = min(w, right + margin_w)
        
        # Extract face region with margin
        face_image = image[top:bottom, left:right]
        
        # Save the image
        output_file = os.path.join(output_path, f"{pose}.png")
        cv2.imwrite(output_file, face_image)
        
        return True
    except Exception as e:
        print(f"Error capturing face: {e}")
        return False

def calculate_eye_aspect_ratio(eye_landmarks):
    """
    Calculate the eye aspect ratio to detect blinks
    """
    vertical_1 = np.linalg.norm(np.array(eye_landmarks[1]) - np.array(eye_landmarks[5]))
    vertical_2 = np.linalg.norm(np.array(eye_landmarks[2]) - np.array(eye_landmarks[4]))
    horizontal = np.linalg.norm(np.array(eye_landmarks[0]) - np.array(eye_landmarks[3]))
    ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
    return ear

def detect_face_orientation(landmarks, image_shape):
    """
    Detect face orientation using Head Pose Estimation (yaw angle).
    Returns: "center", "left", or "right"
    """
    image_points = np.array([
        landmarks['nose_tip'][2],        # Nose tip
        landmarks['chin'][8],            # Chin
        landmarks['left_eye'][0],        # Left eye left corner
        landmarks['right_eye'][3],       # Right eye right corner
        landmarks['top_lip'][0],         # Left mouth corner
        landmarks['top_lip'][6]          # Right mouth corner
    ], dtype="double")

    h, w = image_shape[:2]
    focal_length = w
    center = (w // 2, h // 2)

    camera_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1]
    ], dtype="double")

    dist_coeffs = np.zeros((4,1))

    # 3D model points
    model_points = np.array([
        (0.0, 0.0, 0.0),           # Nose tip
        (0.0, -330.0, -65.0),      # Chin
        (-225.0, 170.0, -135.0),   # Left eye left corner
        (225.0, 170.0, -135.0),    # Right eye right corner
        (-150.0, -150.0, -125.0),  # Left Mouth corner
        (150.0, -150.0, -125.0)    # Right mouth corner
    ])

    success, rotation_vector, translation_vector = cv2.solvePnP(
        model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
    )

    if not success:
        return "unknown"

    # Convert rotation vector to rotation matrix
    rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
    pose_matrix = cv2.hconcat((rotation_matrix, translation_vector))
    _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(pose_matrix)

    yaw = euler_angles[1][0]   # left/right
    pitch = euler_angles[0][0] # up/down
    roll = euler_angles[2][0]  # tilt

    # Tentukan threshold yaw
    YAW_THRESHOLD = 15  # derajat
    
    if yaw > YAW_THRESHOLD:
        return "right"
    elif yaw < -YAW_THRESHOLD:
        return "left"
    else:
        return "center"
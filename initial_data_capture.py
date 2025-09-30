import cv2
import face_recognition
import numpy as np
import os

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


def Intial_data_capture(name=None, camera_id=None):
    """
    Capture reference images with orientation + blink verification
    Args:
        name (str): Name of the user to register
        camera_id (int): Camera device ID to use
    """
    base_path = "Attendance_data/"
    if camera_id == None:
        camera_id = 0  # Use default camera on Windows
    
    # Create base directory if it doesn't exist
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    
    # Check existing names in the Attendance_data folder
    existing_names = []
    for item in os.listdir(base_path):
        if os.path.isdir(os.path.join(base_path, item)):
            existing_names.append(item.lower())  # Store folder names in lowercase
    
    # Validate name input
    if not name:
        print("Error: No name provided!")
        return False
    
    if name.lower() in existing_names:
        print(f"Error: {name} already exists in the database!")
        return False
    
    # Create person-specific directory
    person_path = os.path.join(base_path, name)
    os.makedirs(person_path)

    camera = cv2.VideoCapture(camera_id)
    
    EYE_BLINK_THRESHOLD = 0.25
    ORIENTATION_HOLD_TIME = 2.0
    
    movement_sequence = ["center", "right-capture", "left-capture", "center-blink"]
    current_movement = 0
    movement_start_time = 0
    orientation_confirmed = False
    capture_delay = 0.5  # Reduced from 1.0 to 0.5 seconds
    capture_time = 0
    
    blink_counter = 0
    consecutive_blink_frames = 0
    is_eyes_closed = False
    last_blink_time = 0
    required_blinks = 3
    
    print("\nInstructions:")
    print("1. Look at CENTER for 2 seconds")
    print("2. Turn RIGHT and hold for capture")
    print("3. Turn LEFT and hold for capture")
    print("4. Look at CENTER and blink 3 times")
    print("Press ESC to cancel\n")
    
    while True:
        ret, image = camera.read()
        if not ret:
            print("Failed to grab frame")
            break
            
        small_frame = cv2.resize(image, (0,0), fx=0.25, fy=0.25)
        rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_small, model="hog")
        face_landmarks = face_recognition.face_landmarks(rgb_small)

        display_image = image.copy()
        
        if len(face_locations) > 0 and len(face_landmarks) > 0:
            landmarks = face_landmarks[0]
            current_time = cv2.getTickCount() / cv2.getTickFrequency()
            
            # Scale landmarks back
            scaled_landmarks = {}
            for feature, points in landmarks.items():
                scaled_points = []
                for point in points:
                    scaled_points.append([point[0] * 4, point[1] * 4])
                scaled_landmarks[feature] = scaled_points
            
            # Draw landmarks
            for feature, points in scaled_landmarks.items():
                points = np.array(points)
                cv2.polylines(display_image, [points], True, (0, 255, 0), 2)
                if feature in ['left_eye', 'right_eye', 'nose_tip', 'top_lip', 'bottom_lip']:
                    for point in points:
                        cv2.circle(display_image, (int(point[0]), int(point[1])), 2, (0, 255, 0), -1)
            
            # 🔹 Ganti: pakai Head Pose Estimation
            orientation = detect_face_orientation(scaled_landmarks, image.shape)
            
            height, width = display_image.shape[:2]
            cv2.putText(display_image, f"Current Position: {orientation.upper()}",
                       (width - 300, 30), cv2.FONT_HERSHEY_SIMPLEX,
                       0.7, (0, 255, 255), 2)
            
            # Handle movement sequence
            required_orientation = movement_sequence[current_movement]
            if "center-blink" not in required_orientation:  # Handle all non-blinking movements
                
                # Handle different movement types
                check_orientation = required_orientation.split('-')[0]  # Get base orientation without capture flag
                
                if orientation == check_orientation and not orientation_confirmed:
                    if movement_start_time == 0:
                        movement_start_time = current_time
                    elif (current_time - movement_start_time) >= ORIENTATION_HOLD_TIME:
                        orientation_confirmed = True
                        print(f"{check_orientation.upper()} position confirmed!")
                        if "capture" in required_orientation:
                            capture_time = current_time  # Start capture delay
                else:
                    movement_start_time = 0
                
                # Handle capture delay and process
                if orientation_confirmed and "capture" in required_orientation:
                    if (current_time - capture_time) < capture_delay:
                        # Show countdown
                        remaining_delay = capture_delay - (current_time - capture_time)
                        cv2.putText(display_image, f"Capturing in: {remaining_delay:.1f}s",
                                  (10, 120), cv2.FONT_HERSHEY_SIMPLEX,
                                  0.7, (0, 255, 255), 2)
                    else:
                        # Capture image with appropriate suffix
                        if "right" in required_orientation:
                            cv2.imwrite(os.path.join(person_path, 'right.png'), image)
                            print(f"Right side image captured!")
                        elif "left" in required_orientation:
                            cv2.imwrite(os.path.join(person_path, 'left.png'), image)
                            print(f"Left side image captured!")
                        current_movement += 1
                        orientation_confirmed = False
                        movement_start_time = 0
                elif orientation_confirmed and not "capture" in required_orientation:
                    current_movement += 1
                    orientation_confirmed = False
                    movement_start_time = 0
                
                # Get image dimensions
                height, width = display_image.shape[:2]
                center_x = width // 2
                center_y = height // 2

                # Get instruction based on current required orientation
                check_orientation = required_orientation.split('-')[0]  # Get base orientation
                
                # Set instruction text based on current step
                if check_orientation == "center" and "blink" not in required_orientation:
                    instruction_text = "LOOK AT CENTER"
                elif check_orientation == "right":
                    instruction_text = "TURN RIGHT"
                elif check_orientation == "left":
                    instruction_text = "TURN LEFT"
                
                # Add remaining time if holding position
                if movement_start_time > 0:
                    remaining_time = ORIENTATION_HOLD_TIME - (current_time - movement_start_time)
                    if remaining_time > 0:
                        instruction_text += f" ({remaining_time:.1f}s)"
                
                # Add capture countdown if in capture phase
                if orientation_confirmed and "capture" in required_orientation:
                    remaining_capture = capture_delay - (current_time - capture_time)
                    if remaining_capture > 0:
                        instruction_text += f" - Capturing in {remaining_capture:.1f}s"

                # Draw step and instruction in top left
                progress = f"Step {current_movement + 1} of {len(movement_sequence)}"
                cv2.putText(display_image, progress,
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.7, (255, 255, 255), 2)
                cv2.putText(display_image, instruction_text,
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX,
                           0.7, (0, 255, 255), 2)
            
            else:  # Handle blinking phase
                # Get eye landmarks
                left_eye = landmarks['left_eye']
                right_eye = landmarks['right_eye']
                
                # Calculate eye aspect ratios
                left_ear = calculate_eye_aspect_ratio(left_eye)
                right_ear = calculate_eye_aspect_ratio(right_eye)
                avg_ear = (left_ear + right_ear) / 2.0
                
                if orientation == "center":
                    # Check for blink with debug info
                    cv2.putText(display_image, f"Eye Ratio: {avg_ear:.2f}",
                               (10, 150), cv2.FONT_HERSHEY_SIMPLEX,
                               0.7, (255, 255, 255), 2)
                    
                    # Balanced blink detection
                    if avg_ear < EYE_BLINK_THRESHOLD:
                        consecutive_blink_frames += 1
                        if consecutive_blink_frames >= 2:  # Need 2 frames of closed eyes for confirmation
                            if not is_eyes_closed and (current_time - last_blink_time) > 0.8:  # Need 0.8 seconds between blinks
                                blink_counter += 1
                                last_blink_time = current_time
                                is_eyes_closed = True
                    else:
                        is_eyes_closed = False
                        consecutive_blink_frames = 0
                    
                    # Display blink status in top left
                    progress = f"Step {current_movement + 1} of {len(movement_sequence)}"
                    cv2.putText(display_image, progress,
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                               0.7, (255, 255, 255), 2)
                    cv2.putText(display_image, "Look at CENTER and BLINK",
                               (10, 60), cv2.FONT_HERSHEY_SIMPLEX,
                               0.7, (0, 255, 0), 2)
                    cv2.putText(display_image, f"Blinks: {blink_counter}/{required_blinks}",
                               (10, 90), cv2.FONT_HERSHEY_SIMPLEX,
                               0.7, (0, 255, 0), 2)
                else:
                    progress = f"Step {current_movement + 1} of {len(movement_sequence)}"
                    cv2.putText(display_image, progress,
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                               0.7, (255, 255, 255), 2)
                    cv2.putText(display_image, "Please look at CENTER",
                               (10, 60), cv2.FONT_HERSHEY_SIMPLEX,
                               0.7, (0, 255, 255), 2)
                
                # Check if all conditions are met
                if blink_counter >= required_blinks:
                    # Add delay after last blink
                    if (current_time - last_blink_time) < 1.0:  # Wait for 1 second
                        cv2.putText(display_image, "Get ready for capture...", (10, 120),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    else:
                        cv2.putText(display_image, "CAPTURING!", (10, 120),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        # Save center image
                        cv2.imwrite(os.path.join(person_path, 'center.png'), image)
                        print(f"Center image captured!")
                        print(f"All images captured successfully!")
                        break
        
        # Show the image
        cv2.imshow('Capturing', display_image)
        
        # Check for ESC key
        if cv2.waitKey(1) == 27:  # ESC
            print("Capture cancelled")
            break
    
    # Cleanup
    camera.release()
    cv2.destroyAllWindows()
    
    # Automatically run main.py after successful capture
    print("\nStarting attendance system...")
    import subprocess
    import sys
    subprocess.Popen([sys.executable, "main.py"])

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        name = sys.argv[1]
        Intial_data_capture(name)
    else:
        print("Error: Please provide a name as argument")
        sys.exit(1)

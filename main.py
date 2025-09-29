
import cv2
import numpy as np
import face_recognition
import os
import time
from datetime import datetime
from datetime import date
import pytz
import csv

# Hardware acceleration configuration
HARDWARE_CODEC = {
    'backend': cv2.CAP_FFMPEG,
    'codec': cv2.VideoWriter_fourcc(*'H264'),  # H.264 codec for NVIDIA acceleration
    'buffersize': 1024*64,  # 64KB buffer
    'extra_options': {}
}


def identifyEncodings(images, classNames):
    '''
    Encoding is Recognition and comparing particular face in database or stored folder

    args:
    images: list of images
    classNames: list of image names
    '''
    
    encodeList = []
    for img, name in zip(images, classNames):
        small_frame = cv2.resize(img, (0,0), fx=0.25, fy=0.25)
        img = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(img)
        if len(encodings) > 0:
            encode = encodings[0]
            encodeList.append(encode)
        else:
            print(f"Warning: No face detected in image for {name}")
            # Remove the corresponding name from classNames
            classNames.remove(name)
            continue
    return encodeList

def markAttendance(name):
    '''
    This function handles attendance marking in CSV file and notifies the API
    
    args:
    name: str
    '''
    try:
        # Ensure the directory exists
        os.makedirs("Attendance_Entry", exist_ok=True)
        
        # Use a fixed filename for today's date
        now = datetime.now()
        current_date = now.strftime("%y_%m_%d")
        attendance_file = f'Attendance_Entry/Attendance_{current_date}.csv'
        
        # Create file with headers if it doesn't exist
        if not os.path.exists(attendance_file):
            with open(attendance_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "Time", "Date"])
        
        # Record the attendance
        time_str = now.strftime('%H:%M:%S')
        date_str = now.strftime('%Y-%m-%d')
        
        with open(attendance_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([name, time_str, date_str])
        print(f"Logged attendance for {name} at {time_str}")
        
        # Attempt to notify the API
        try:
            import requests
            requests.post("http://localhost:8000/attendance", 
                        json={"name": name, "time": time_str, "date": date_str})
        except:
            print("Failed to notify API, but attendance was logged locally")
    
    except Exception as e:
        print(f"Error marking attendance: {e}")
        # If there's an error, try using a backup file
        try:
            backup_file = "Attendance_Entry/Attendance_Backup.csv"
            with open(backup_file, 'a', newline='') as f:
                writer = csv.writer(f)
                if f.tell() == 0:  # If file is empty, write header
                    writer.writerow(["Name", "Time", "Date"])
                writer.writerow([name, now.strftime('%H:%M:%S'), now.strftime('%Y-%m-%d')])
            print("Logged to backup file instead")
        except Exception as backup_error:
            print(f"Failed to write to backup file: {backup_error}")

# Ensure Attendance_Entry directory exists
os.makedirs("Attendance_Entry", exist_ok=True)

# Create today's attendance file
current_date = datetime.now().strftime("%y_%m_%d")
attendance_file = f"Attendance_Entry/Attendance_{current_date}.csv"

# Create file with headers if it doesn't exist
if not os.path.exists(attendance_file):
    with open(attendance_file, "w", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Time", "Date"])
    print(f"Created new attendance file for today: {attendance_file}")
else:
    print(f"Using today's attendance file: {attendance_file}")

#Preprocessing the data 

path = 'Attendance_data'
images = []
classNames = []
# Get list of person folders
myList = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
print("Found persons:", myList)

# Process each person's folder
for person_folder in myList:
    person_path = os.path.join(path, person_folder)
    # Look for all pose images (center, left, right)
    for pose in ['center.png', 'left.png', 'right.png']:
        pose_path = os.path.join(person_path, pose)
        if os.path.exists(pose_path):
            curImg = cv2.imread(pose_path)
            if curImg is not None:
                images.append(curImg)
                classNames.append(person_folder)  # Use folder name as class name
print("Loaded persons:", classNames)
print(f"Total images loaded: {len(images)} (including all poses)")

# Encoding of input image data
encodeListKnown = identifyEncodings(images, classNames)
print('Encoding Complete')
print(f'Successfully encoded {len(encodeListKnown)} faces')


# Set CUDA device if available
if cv2.cuda.getCudaEnabledDeviceCount() > 0:
    cv2.cuda.setDevice(0)
    print("Using GPU acceleration")
else:
    print("Using CPU processing")

# Function to check if mouse click is within button bounds
def is_mouse_click_in_button(x, y, button_pos):
    bx, by, bw, bh = button_pos
    return bx <= x <= bx + bw and by <= y <= by + bh

# Mouse callback function
def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        button_pos = param
        if is_mouse_click_in_button(x, y, button_pos):
            print("\nStarting registration process...")
            cap.release()
            cv2.destroyAllWindows()
            # Use subprocess.run to wait for the process to complete
            import subprocess
            import sys
            try:
                subprocess.run([sys.executable, "initial_data_capture.py"], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error running registration: {e}")
            global running
            running = False

#Camera capture 
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Create window and set mouse callback
cv2.namedWindow('Attendance System')
button_pos = (10, 440, 150, 30)  # x, y, width, height
cv2.setMouseCallback('Attendance System', mouse_callback, button_pos)

last_detected_name = None
last_detect_time = 0
CACHE_TIME = 2.0  # detik, cache nama wajah biar gak dihitung ulang tiap frame
running = True

while running:
    success, img = cap.read()
    if not success:
        break
        
    # Draw registration button
    x, y, w, h = button_pos
    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), cv2.FILLED)
    cv2.putText(img, "Register New", (x + 5, y + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Process image
    small_frame = cv2.resize(img, (0, 0), fx=0.25, fy=0.25)
    rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    # Detect faces
    facesCurFrame = face_recognition.face_locations(rgb_small, model="hog")
    
    # Check number of faces and show appropriate status message
    if len(facesCurFrame) > 1:
        cv2.putText(img, "Multiple faces detected!", 
                (10, 30), cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 0, 255), 2)
    elif len(facesCurFrame) == 0:
        cv2.putText(img, "No face detected", (10, 30),
                cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 255, 255), 2)
    # Only process and show frame when exactly one face is detected
    elif len(facesCurFrame) == 1:
        encodesCurFrame = face_recognition.face_encodings(rgb_small, facesCurFrame)
        
        # Process the single detected face
        if len(encodesCurFrame) > 0:
            encodeFace = encodesCurFrame[0]
            faceLoc = facesCurFrame[0]
            name = "Unknown"
            
            # Check for face match
            if len(encodeListKnown) > 0:
                faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
                matchIndex = np.argmin(faceDis)
                if faceDis[matchIndex] < 0.4:  # strict threshold for better accuracy
                    name = classNames[matchIndex]
                    markAttendance(name)
                    
                    # Draw green frame for recognized face
                    top, right, bottom, left = [coord * 4 for coord in faceLoc]
                    cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.rectangle(img, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
                    cv2.putText(img, name, (left + 6, bottom - 6),
                            cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)

    # Display the result
    cv2.imshow('Attendance System', img)
    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()

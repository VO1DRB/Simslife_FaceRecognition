# **FACE BASED ATTENDANCE SYSTEM**

## **OBJECTIVE:**

1. A face based attendance system incorporates facial recognition technology to recognize and verify an employee's or student facial features and to record attendance automatically. 

2. A facial recognition attendance system is a non-contact approach to managing employees in a business significantly, when they are out on the field.

## **PROJECT STRUCTURE:**

```
Simslife_FaceRecognition/
├── dashboard/              # Streamlit dashboard application
│   ├── app.py              # Main dashboard application
│   ├── pages/              # Dashboard pages
│   │   └── attendance.py   # Attendance page
│   └── utils/              # Utility functions
│       ├── face_recognition_utils/  # Face recognition utilities
│       │   ├── __init__.py          # Face recognition module initialization
│       │   └── core.py              # Core face recognition functionality
│       ├── image_management.py      # Image management utilities
│       ├── sound.py                 # Sound effects
│       └── user_data.py             # User data management
├── Attendance_data/        # Face image storage
├── Attendance_Entry/       # Attendance records (CSV files)
└── api/                    # API module
    ├── auth.py             # Authentication API
    ├── database.py         # Database interface
    └── models.py           # Data models
```ASED ATTENDANCE SYSTEM USING NVIDIA JETSON AGX XAVIER DEVICE**

![20230409_100542_1](https://user-images.githubusercontent.com/75832198/230754595-8df2c106-41a3-4782-acce-9d3b63601444.jpg)


## **OBJECTIVE:**

1. A face based attendance system incorporates facial recognition technology to recognize and verify an employee’s or student facial features and to record attendance automatically. 

2. A facial recognition attendance system is a non-contact approach to managing employees in a business significantly, when they are out on the field.


## **FEATURES:**

- **User Registration**: Register users with multiple face poses (center, left, right) for better recognition
- **Attendance Tracking**: Real-time face recognition for attendance check-in and check-out
- **Shift Management**: Support for morning and night shifts
- **Attendance History**: View and analyze attendance records with data visualizations
- **User Management**: Add, edit, and delete user information
- **Dashboard**: Web-based interface for all system functions

## **SETUP AND INSTALLATION:**

### **1. Install prerequisite libraries**

```bash
$ pip install -r requirements.txt
```
Make sure OpenCV, NumPy, face_recognition, and Streamlit are installed.

### **2. Take pictures for user registration**

Two ways to register users:

#### Option 1: Using the command line
```bash
$ python initial_data_capture.py
```
Follow the prompts to capture face images in different poses.

#### Option 2: Using the Streamlit dashboard (recommended)
```bash
$ cd dashboard
$ streamlit run app.py
```
Navigate to the "Register New User" section and follow the guided registration process.

### **3. Running the attendance system**

#### Using the Streamlit dashboard (recommended)
```bash
$ cd dashboard
$ streamlit run app.py
```
Navigate to the "Attendance" page to check in and out.

## **ATTENDANCE DASHBOARD**

The system features a comprehensive dashboard for all attendance management tasks:

### **Dashboard Features:**

1. **Home Page**: Overview of system statistics
2. **Attendance Page**: 
   - Real-time face recognition for attendance
   - Historical attendance records with visualizations
3. **User Management**: 
   - Register new users
   - Edit user information
   - Delete users
   - Manage user face images
4. **Reports**: 
   - Generate attendance reports
   - Export data as CSV

### **Managing User Images:**

#### **Using the Dashboard**
1. Navigate to the User Management section
2. Select a user to manage
3. You can view, add, or delete user face images

#### **Using Command Line**
For advanced users or batch operations:
```bash
$ python delete_image.py
```
Follow the prompts to delete a specific user's images.

#### **Image Types**
The system supports two types of user images:
- **Single Image**: Basic recognition with one frontal image
- **Multiple Pose Images**: Enhanced recognition with center, left, and right poses

## **OPTIMIZATIONS:**

The project has been optimized with:
- Consolidated face recognition utilities
- Streamlined interface for better user experience
- Enhanced visualizations for attendance data
- Improved code organization and documentation
- Real-time camera processing for better recognition

5. If you want to delete the image throughout the folder use 5th step mentioned above.

## **💡Process of Certification💡**

🧑‍💻Github: https://lnkd.in/gyZVFFGk

📃Article link: https://lnkd.in/g8gHXApR

😍Youtube: https://lnkd.in/gfz7g4C6

## **Finally Accomplished! APR 2023**

![1681444951827](https://github.com/VK-Ant/AttendanceSystem-JetsonAGX/assets/75832198/7fd2fe7b-a806-4c7e-a843-760ee05c5bb2)


### **THANK YOU & CREDIT**

1. HarishKumar, Venkatesan (Providing Data and taking demo output video) 
2. BSS.Narayan (Providing the development kit)

## **🤗Happy learning🤗**

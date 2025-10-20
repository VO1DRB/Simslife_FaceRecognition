from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pathlib import Path
import sys
import os
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from datetime import datetime, timedelta
import subprocess
import sqlite3
from typing import List
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI(title="SIMSLIFE Face Recognition API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Configuration
SECRET_KEY = "your-secret-key-here"  # Change this in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Database Models (DEFINISI HANYA SEKALI)
class User(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class AttendanceRecord(BaseModel):
    id: int
    employee_name: str
    timestamp: datetime
    status: str

# Database Setup (DEFINISI HANYA SEKALI)
def init_db():
    conn = sqlite3.connect('attendance.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users
        (username TEXT PRIMARY KEY, password TEXT)
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         employee_name TEXT,
         timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
         status TEXT)
    ''')
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Authentication Functions
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "SIMSLIFE Face Recognition API",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "token": "/token",
            "capture": "/capture/{name}",
            "attendance": "/attendance",
            "all_attendance": "/attendance/all"
        }
    }

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Simple authentication - replace with database check in production
    if form_data.username == "admin" and form_data.password == "password":
        access_token = create_access_token(
            data={"sub": form_data.username}
        )
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(
        status_code=400,
        detail="Incorrect username or password"
    )

@app.post("/capture/{name}")
async def capture_face(name: str, current_user: str = Depends(get_current_user)):
    try:
        # Get the root directory path
        root_dir = Path(__file__).parent
        script_path = root_dir / "initial_data_capture.py"
        
        # Validate script exists
        if not script_path.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Capture script not found at: {script_path}"
            )
        
        # Run the face capture script with explicit Python interpreter
        result = subprocess.run(
            [sys.executable, str(script_path), name],
            capture_output=True,
            text=True,
            cwd=str(root_dir),
            timeout=60  # Add timeout
        )
        
        if result.returncode == 0:
            return {
                "message": f"Face captured successfully for {name}",
                "output": result.stdout
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Face capture failed: {result.stderr}"
            )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Face capture timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/attendance")
async def mark_attendance(current_user: str = Depends(get_current_user)):
    try:
        # Get root directory and script path
        root_dir = Path(__file__).parent
        script_path = root_dir / "main.py"
        
        if not script_path.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Main script not found at: {script_path}"
            )
        
        # Run the main recognition script with explicit working directory
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=str(root_dir),
            timeout=60  # Add timeout
        )
        
        if result.returncode == 0:
            # Save attendance record
            conn = sqlite3.connect('attendance.db')
            c = conn.cursor()
            employee_name = result.stdout.strip() or "Unknown"
            c.execute(
                "INSERT INTO attendance (employee_name, status) VALUES (?, ?)",
                (employee_name, "present")
            )
            conn.commit()
            conn.close()
            return {
                "message": "Attendance marked successfully",
                "employee": employee_name
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Attendance marking failed: {result.stderr}"
            )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Attendance recognition timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/attendance/all")
async def get_all_attendance(current_user: str = Depends(get_current_user)):
    try:
        conn = sqlite3.connect('attendance.db')
        c = conn.cursor()
        c.execute("SELECT * FROM attendance ORDER BY timestamp DESC")
        records = c.fetchall()
        conn.close()
        
        attendance_records = []
        for record in records:
            attendance_records.append({
                "id": record[0],
                "employee_name": record[1],
                "timestamp": record[2],
                "status": record[3]
            })
        return attendance_records
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    print("Starting SIMSLIFE Face Recognition API...")
    print("API will be available at: http://localhost:8000")
    print("API Documentation at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
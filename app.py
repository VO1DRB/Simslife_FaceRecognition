from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from datetime import datetime, timedelta
import subprocess
import sqlite3
from typing import List
from pydantic import BaseModel

app = FastAPI()

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

# Database Models
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

# Database Setup
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
        # Run the face capture script
        result = subprocess.run(
            ["python", "initial_data_capture.py", name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return {"message": f"Face captured successfully for {name}"}
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Face capture failed: {result.stderr}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/attendance")
async def mark_attendance(current_user: str = Depends(get_current_user)):
    try:
        # Run the main recognition script
        result = subprocess.run(
            ["python", "main.py"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            # Save attendance record
            conn = sqlite3.connect('attendance.db')
            c = conn.cursor()
            c.execute(
                "INSERT INTO attendance (employee_name, status) VALUES (?, ?)",
                (result.stdout.strip(), "present")
            )
            conn.commit()
            conn.close()
            return {"message": "Attendance marked successfully"}
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Attendance marking failed: {result.stderr}"
            )
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
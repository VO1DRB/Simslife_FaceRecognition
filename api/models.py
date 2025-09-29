from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class User(BaseModel):
    username: str
    full_name: str
    role: str  # 'admin' or 'user'
    shift: str  # 'morning' or 'night'
    is_active: bool = True

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class AttendanceRecord(BaseModel):
    employee_name: str
    date: datetime
    check_in: Optional[datetime]
    check_out: Optional[datetime]
    shift: str
    status: str  # 'on_time', 'late', 'invalid', 'absent'
    device_id: str

class DeviceInfo(BaseModel):
    device_id: str
    name: str
    location: str
    last_active: datetime
    status: str  # 'active' or 'inactive'
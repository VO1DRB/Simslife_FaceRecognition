from datetime import datetime, time
from typing import Tuple

def is_within_shift_hours(current_time: datetime, shift: str) -> bool:
    """Check if current time is within shift hours"""
    current_hour = current_time.hour
    
    if shift == "morning":
        return 8 <= current_hour < 17
    elif shift == "night":
        return 17 <= current_hour < 22
    return False

def get_shift_status(checkin_time: datetime, current_time: datetime = None) -> Tuple[str, str]:
    """
    Get the shift and attendance status based on check-in time
    
    Returns:
        Tuple[str, str]: (shift_type, status)
        shift_type: "morning" or "night"
        status: "early", "ontime", "late", or "wrong_shift"
    """
    if current_time is None:
        current_time = datetime.now()
        
    checkin_hour = checkin_time.hour
    
    # Morning shift (8:00 - 17:00)
    if 5 <= checkin_hour < 17:
        if checkin_hour < 8:
            return "morning", "early"
        elif checkin_hour == 8:
            return "morning", "ontime"
        else:
            return "morning", "late"
            
    # Night shift (17:00 - 22:00)
    elif 17 <= checkin_hour < 22:
        if checkin_hour == 17:
            return "morning", "ontime"
        else:
            return "night", "late"
            
    return "unknown", "wrong_shift"

def should_auto_checkout(checkin_time: datetime, current_time: datetime = None) -> bool:
    """
    Determine if user should be automatically checked out based on shift end time
    """
    if current_time is None:
        current_time = datetime.now()
        
    shift, _ = get_shift_status(checkin_time)
    
    if shift == "morning":
        shift_end = time(17, 0)  # 17:00
    elif shift == "night":
        shift_end = time(22, 0)  # 22:00
    else:
        return False
        
    current_time_only = current_time.time()
    return current_time_only >= shift_end
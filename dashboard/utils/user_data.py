import json
from pathlib import Path

__all__ = ['delete_user_completely', 'get_user_data']

def delete_user_completely(username: str) -> tuple[bool, str]:
    """
    Delete user data completely from the system, including:
    - API database entry
    - user_data.json entries
    - Image files
    - Image folders
    
    Returns:
        tuple[bool, str]: (success, message)
    """
    try:
        import requests
        import shutil
        from pathlib import Path
        
        # 1. Delete from API first using admin auth
        try:
            # First get admin token
            auth_response = requests.post(
                "http://localhost:8000/token",
                data={
                    "username": "admin",  # Admin credentials should be configured
                    "password": "admin123"
                }
            )
            
            if auth_response.status_code != 200:
                return False, "Failed to authenticate with API"
                
            token = auth_response.json()["access_token"]
            
            # Now delete with auth token
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.delete(
                f"http://localhost:8000/users/{username}",
                headers=headers
            )
            
            if response.status_code != 200:
                return False, f"Failed to delete user from API: {response.text}"
        except requests.exceptions.RequestException as e:
            return False, f"API Error: {e}"

        # 2. Get the paths
        root_dir = Path(__file__).parent.parent.parent
        dashboard_dir = Path(__file__).parent.parent

        # 3. Delete from user_data.json files
        json_files = [
            root_dir / "user_data.json",
            dashboard_dir / "user_data.json"
        ]
        
        for json_path in json_files:
            if json_path.exists():
                try:
                    with open(json_path, 'r') as f:
                        data = json.load(f)
                    if username in data:
                        del data[username]
                        with open(json_path, 'w') as f:
                            json.dump(data, f, indent=4)
                except Exception as e:
                    return False, f"Error updating {json_path}: {e}"
                    
        # 4. Delete image files
        attendance_dirs = [
            root_dir / "Attendance_data",
            dashboard_dir / "Attendance_data"
        ]
        
        for att_dir in attendance_dirs:
            if not att_dir.exists():
                continue
                
            # Check for single image
            single_img = att_dir / f"{username}.png"
            if single_img.exists():
                try:
                    single_img.unlink()
                except Exception as e:
                    return False, f"Error deleting image {single_img}: {e}"
                
            # Check for image folder
            user_folder = att_dir / username
            if user_folder.exists():
                try:
                    shutil.rmtree(user_folder)
                except Exception as e:
                    return False, f"Error deleting folder {user_folder}: {e}"
                    
        return True, "User deleted successfully"
        
    except Exception as e:
        return False, f"Unexpected error: {e}"
    
    # Remove from user_data.json
    user_data_files = [
        root_dir / "user_data.json",
        dashboard_dir / "user_data.json"
    ]

    for user_data_file in user_data_files:
        if user_data_file.exists():
            try:
                with open(user_data_file, 'r') as f:
                    data = json.load(f)
                if username in data:
                    del data[username]
                    with open(user_data_file, 'w') as f:
                        json.dump(data, f, indent=4)
            except Exception as e:
                print(f"Error updating {user_data_file}: {e}")

    # Clean up image files
    attendance_dirs = [
        root_dir / "Attendance_data",
        dashboard_dir / "Attendance_data"
    ]

    for attendance_dir in attendance_dirs:
        if not attendance_dir.exists():
            continue

        # Delete single image if exists
        single_image = attendance_dir / f"{username}.png"
        if single_image.exists():
            try:
                single_image.unlink()
            except Exception as e:
                print(f"Error deleting {single_image}: {e}")

        # Delete folder if exists
        user_folder = attendance_dir / username
        if user_folder.exists():
            try:
                for img in user_folder.glob("*.png"):
                    img.unlink()
                user_folder.rmdir()
            except Exception as e:
                print(f"Error deleting folder {user_folder}: {e}")

def get_user_data():
    """Get user data from json file"""
    # First try root directory
    root_data = Path(__file__).parent.parent / "user_data.json"
    if root_data.exists():
        try:
            with open(root_data, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading root user data: {e}")
    
    # Then try dashboard directory
    dashboard_data = Path(__file__).parent / "user_data.json"
    if dashboard_data.exists():
        try:
            with open(dashboard_data, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading dashboard user data: {e}")
    
    return {}
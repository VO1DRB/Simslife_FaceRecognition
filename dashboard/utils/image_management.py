import json
from pathlib import Path
import streamlit as st

def delete_user_image(username: str, image_type: str = None, delete_all: bool = False) -> tuple[bool, str]:
    """
    Delete specific user image(s) without removing the entire user.
    This is useful for deleting individual pose images from multiple image users.
    
    Args:
        username: The username whose image(s) to delete
        image_type: The type of image to delete ('center', 'left', 'right', or None for single image)
        delete_all: If True, delete all images but keep the user entry
        
    Returns:
        tuple[bool, str]: (success, message)
    """
    try:
        # Get the paths
        root_dir = Path(__file__).parent.parent.parent
        dashboard_dir = Path(__file__).parent.parent
        
        # Define the attendance directories - try both parent and current directory
        attendance_dirs = []
        
        # First check if main project Attendance_data exists
        if (root_dir / "Attendance_data").exists():
            attendance_dirs.append(root_dir / "Attendance_data")
        
        # Then check dashboard Attendance_data
        if (dashboard_dir / "Attendance_data").exists():
            attendance_dirs.append(dashboard_dir / "Attendance_data")
            
        if not attendance_dirs:
            print("No Attendance_data directories found!")
            return False, "No Attendance_data directories found"
        
        images_deleted = 0
        delete_errors = []
        
        for att_dir in attendance_dirs:
            print(f"Checking directory: {att_dir}")
                
            user_folder = att_dir / username
            single_img = att_dir / f"{username}.png"
            
            # Case 1: Delete single image 
            if (image_type is None or image_type == "single") and single_img.exists():
                try:
                    single_img.unlink()
                    images_deleted += 1
                    print(f"Deleted single image: {single_img}")
                except Exception as e:
                    error_msg = f"Error deleting image {single_img}: {e}"
                    print(error_msg)
                    delete_errors.append(error_msg)
            
            # Case 2: Delete specific pose image
            elif image_type and user_folder.exists():
                image_path = user_folder / f"{image_type}.png"
                if image_path.exists():
                    try:
                        image_path.unlink()
                        images_deleted += 1
                        print(f"Deleted {image_type} image for {username}")
                    except Exception as e:
                        error_msg = f"Error deleting {image_type} image: {e}"
                        print(error_msg)
                        delete_errors.append(error_msg)
            
            # Case 3: Delete all images in user folder
            elif delete_all and user_folder.exists():
                for img in user_folder.glob("*.png"):
                    try:
                        img.unlink()
                        images_deleted += 1
                        print(f"Deleted image: {img}")
                    except Exception as e:
                        error_msg = f"Error deleting {img}: {e}"
                        print(error_msg)
                        delete_errors.append(error_msg)
                        
                # Also try to delete single image if it exists
                if single_img.exists():
                    try:
                        single_img.unlink()
                        images_deleted += 1
                        print(f"Deleted single image: {single_img}")
                    except Exception as e:
                        error_msg = f"Error deleting single image: {e}"
                        print(error_msg)
                        delete_errors.append(error_msg)
        
        if images_deleted > 0:
            if delete_errors:
                return True, f"Deleted {images_deleted} image(s) with some errors"
            return True, f"Deleted {images_deleted} image(s) successfully"
        else:
            if delete_errors:
                return False, "Failed to delete images: " + ", ".join(delete_errors[:2])
            return False, "No images found to delete"
            
    except Exception as e:
        print(f"Unexpected error in delete_user_image: {e}")
        import traceback
        print(traceback.format_exc())
        return False, f"Unexpected error: {e}"

def get_user_images(username: str) -> list:
    """
    Get all images for a specific user from all possible directories
    
    Args:
        username: The username to get images for
        
    Returns:
        list: List of dictionaries with image path and type
    """
    try:
        # Get paths from both possible locations
        root_dir = Path(__file__).parent.parent.parent
        dashboard_dir = Path(__file__).parent.parent
        
        # Define the attendance directories to check
        attendance_dirs = []
        
        # Check both possible locations
        if (root_dir / "Attendance_data").exists():
            attendance_dirs.append(root_dir / "Attendance_data")
        
        if (dashboard_dir / "Attendance_data").exists():
            attendance_dirs.append(dashboard_dir / "Attendance_data")
            
        if not attendance_dirs:
            print("No Attendance_data directories found!")
            return []
        
        images = []
        
        # Check all directories
        for attendance_dir in attendance_dirs:
            print(f"Checking for images in: {attendance_dir}")
            
            # Check for folder-based user (multiple images)
            user_folder = attendance_dir / username
            
            if user_folder.exists() and user_folder.is_dir():
                # Check for standard poses
                for pose_type in ['center', 'left', 'right']:
                    pose_path = user_folder / f"{pose_type}.png"
                    if pose_path.exists():
                        images.append({
                            "path": str(pose_path),
                            "type": pose_type,
                            "format": "multiple"
                        })
                
                # Check for any other images
                for img_path in user_folder.glob("*.png"):
                    img_type = img_path.stem
                    if img_type not in ['center', 'left', 'right']:
                        images.append({
                            "path": str(img_path),
                            "type": img_type,
                            "format": "multiple"
                        })
            
            # Check for single image user
            single_img = attendance_dir / f"{username}.png"
            if single_img.exists():
                images.append({
                    "path": str(single_img),
                    "type": "single",
                    "format": "single"
                })
                
        # Remove any duplicates based on path
        unique_images = []
        seen_paths = set()
        
        for img in images:
            if img["path"] not in seen_paths:
                seen_paths.add(img["path"])
                unique_images.append(img)
            
        return unique_images
        
    except Exception as e:
        print(f"Error getting user images: {e}")
        import traceback
        print(traceback.format_exc())
        return []
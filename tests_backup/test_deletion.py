"""
Test script for user deletion functionality.
This will create a test user, then delete it to verify the deletion process.
"""
import os
import sys
from pathlib import Path
import json
import shutil
import time

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / "dashboard"))

def create_test_user(username="TEST_USER"):
    """Create a test user for deletion testing"""
    print(f"\n=== Creating test user: {username} ===")
    
    # 1. Create directory structure
    attendance_dir = current_dir / "Attendance_data"
    if not attendance_dir.exists():
        print(f"Creating directory: {attendance_dir}")
        attendance_dir.mkdir(exist_ok=True)
    
    # Create test image file
    test_img_path = attendance_dir / f"{username}.png"
    
    # Create a simple test image
    try:
        # Copy an existing image if available
        existing_images = list(attendance_dir.glob("*.png"))
        if existing_images:
            source_img = existing_images[0]
            shutil.copy2(source_img, test_img_path)
            print(f"Created test image by copying {source_img} to {test_img_path}")
        else:
            # Create an empty file
            with open(test_img_path, 'wb') as f:
                f.write(b'TEST_IMAGE')
            print(f"Created empty test image: {test_img_path}")
    except Exception as e:
        print(f"Error creating test image: {e}")
        return False
    
    # Add to user_data.json
    json_path = current_dir / "user_data.json"
    try:
        data = {}
        if json_path.exists():
            with open(json_path, 'r') as f:
                data = json.load(f)
        
        # Add test user
        data[username] = {
            "role": "Test User",
            "shift": "Test"
        }
        
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=4)
        
        print(f"Added {username} to user_data.json")
    except Exception as e:
        print(f"Error updating user_data.json: {e}")
    
    return test_img_path.exists()

def delete_test_user(username="TEST_USER"):
    """Delete the test user using the delete_user_completely function"""
    print(f"\n=== Deleting test user: {username} ===")
    
    try:
        # Import the function
        from dashboard.utils import delete_user_completely
        
        # Delete the user
        print(f"Calling delete_user_completely({username})...")
        success, message = delete_user_completely(username)
        
        print(f"Result: success={success}, message={message}")
        
        # Verify deletion
        attendance_dir = current_dir / "Attendance_data"
        test_img_path = attendance_dir / f"{username}.png"
        user_folder = attendance_dir / username
        
        json_path = current_dir / "user_data.json"
        user_in_json = False
        
        if json_path.exists():
            with open(json_path, 'r') as f:
                data = json.load(f)
                user_in_json = username in data
        
        if test_img_path.exists():
            print(f"❌ Image still exists: {test_img_path}")
        else:
            print(f"✅ Image deleted: {test_img_path}")
            
        if user_folder.exists():
            print(f"❌ User folder still exists: {user_folder}")
        else:
            print(f"✅ User folder not present: {user_folder}")
            
        if user_in_json:
            print(f"❌ User still in user_data.json: {username}")
        else:
            print(f"✅ User removed from user_data.json: {username}")
        
        return success and not test_img_path.exists() and not user_in_json
        
    except Exception as e:
        print(f"Error in delete_test_user: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def run_test():
    """Run the full test cycle"""
    username = "TEST_USER"
    
    # First, make sure the test user doesn't already exist
    from dashboard.utils import delete_user_completely
    delete_user_completely(username)
    
    # Create test user
    if create_test_user(username):
        print("✅ Test user created successfully")
        
        # Wait a moment to ensure file operations complete
        time.sleep(1)
        
        # Delete test user
        if delete_test_user(username):
            print("\n✅ TEST PASSED: User deletion successful")
        else:
            print("\n❌ TEST FAILED: User deletion issues")
    else:
        print("❌ Failed to create test user")

if __name__ == "__main__":
    run_test()
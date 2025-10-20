"""
Simple test script for image deletion functionality
This standalone script tests the image deletion functions directly
"""
import os
import sys
import json
import shutil
from pathlib import Path

def list_user_images(username):
    """List all images for a specific user"""
    
    # Get paths from both possible locations
    root_dir = Path.cwd()
    attendance_dir = root_dir / "Attendance_data"
    
    if not attendance_dir.exists():
        print(f"Attendance directory not found: {attendance_dir}")
        return []
    
    images = []
    
    # Check for folder-based user (multiple images)
    user_folder = attendance_dir / username
    
    if user_folder.exists() and user_folder.is_dir():
        print(f"Found user folder: {user_folder}")
        # Check for standard poses
        for pose_type in ['center', 'left', 'right']:
            pose_path = user_folder / f"{pose_type}.png"
            if pose_path.exists():
                print(f"Found {pose_type} image: {pose_path}")
                images.append({
                    "path": str(pose_path),
                    "type": pose_type
                })
            else:
                print(f"No {pose_type} image found")
        
        # Check for any other images
        for img_path in user_folder.glob("*.png"):
            if img_path.stem not in ['center', 'left', 'right']:
                print(f"Found other image: {img_path}")
                images.append({
                    "path": str(img_path),
                    "type": img_path.stem
                })
    else:
        print(f"User folder not found: {user_folder}")
    
    # Check for single image user
    single_img = attendance_dir / f"{username}.png"
    if single_img.exists():
        print(f"Found single image: {single_img}")
        images.append({
            "path": str(single_img),
            "type": "single"
        })
    else:
        print(f"No single image found: {single_img}")
            
    return images

def delete_user_image(username, image_type=None):
    """
    Delete a specific user image
    """
    try:
        # Get paths
        root_dir = Path.cwd()
        attendance_dir = root_dir / "Attendance_data"
        
        if not attendance_dir.exists():
            print(f"Error: Attendance directory not found: {attendance_dir}")
            return False
            
        # Handle multiple-image user
        if image_type in ['center', 'left', 'right']:
            user_folder = attendance_dir / username
            image_path = user_folder / f"{image_type}.png"
            
            if image_path.exists():
                print(f"Deleting image: {image_path}")
                image_path.unlink()
                return True
            else:
                print(f"Image not found: {image_path}")
                return False
        
        # Handle single-image user
        elif image_type == 'single':
            single_img = attendance_dir / f"{username}.png"
            
            if single_img.exists():
                print(f"Deleting image: {single_img}")
                single_img.unlink()
                return True
            else:
                print(f"Image not found: {single_img}")
                return False
                
        else:
            print(f"Invalid image type: {image_type}")
            return False
            
    except Exception as e:
        print(f"Error deleting image: {e}")
        return False

def test_delete_and_restore():
    """Test deleting and then restoring a test image"""
    
    # Choose a test user with multiple images - we'll use dimas for testing
    test_user = "dimas"
    test_pose = "left"
    
    # Get the original image path
    root_dir = Path.cwd()
    attendance_dir = root_dir / "Attendance_data"
    user_folder = attendance_dir / test_user
    image_path = user_folder / f"{test_pose}.png"
    backup_path = image_path.with_suffix(".png.bak")
    
    if not image_path.exists():
        print(f"Test image not found: {image_path}")
        return False
    
    try:
        # Create backup
        print(f"Creating backup: {backup_path}")
        shutil.copy2(image_path, backup_path)
        
        # Test deletion
        print(f"Testing deletion of {test_pose} image for {test_user}")
        success = delete_user_image(test_user, test_pose)
        
        if success:
            print("✅ Image deleted successfully")
            
            # Verify image is gone
            if not image_path.exists():
                print("✅ Verified image no longer exists")
            else:
                print("❌ Image still exists after deletion")
        else:
            print("❌ Image deletion failed")
            
        # Wait for verification
        input("Press Enter to restore the image...")
        
        # Restore from backup
        print(f"Restoring image from backup")
        shutil.copy2(backup_path, image_path)
        backup_path.unlink()
        
        if image_path.exists():
            print("✅ Image restored successfully")
        else:
            print("❌ Failed to restore image")
            
        return success
        
    except Exception as e:
        print(f"Test error: {e}")
        
        # Try to restore backup if it exists
        if backup_path.exists():
            try:
                shutil.copy2(backup_path, image_path)
                backup_path.unlink()
                print("⚠️ Restored image from backup after error")
            except:
                print("⚠️ Failed to restore backup")
        
        return False

def test_image_functions():
    """Run simple tests on image deletion functionality"""
    
    print("\n=== Testing Image Functions ===")
    
    # Test users
    test_users = ["KAKA", "MICHAEL", "PATRIA", "dimas"]
    
    for user in test_users:
        print(f"\nTesting with user: {user}")
        
        # List images
        user_images = list_user_images(user)
        
        if not user_images:
            print(f"No images found for {user}, skipping test")
            continue
        
        print(f"Found {len(user_images)} images for {user}")
    
    # Test deletion with restoration
    print("\n=== Testing Image Deletion with Restoration ===")
    test_delete_and_restore()
        
    print("\n=== Test Completed ===")

if __name__ == "__main__":
    test_image_functions()
"""
Test script for image deletion functionality
This script tests the image deletion functions to ensure they work properly
"""
import os
import sys
from pathlib import Path

# Add the current directory and dashboard to path so we can import modules
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir / "dashboard"))

# Import directly from the image_management module
from dashboard.utils.image_management import delete_user_image, get_user_images

def test_get_user_images():
    """Test that we can get user images"""
    print("\n=== Testing get_user_images ===")
    
    # Test for a user that should exist
    test_users = ["KAKA", "MICHAEL", "PATRIA", "dimas"]
    
    for user in test_users:
        print(f"\nChecking images for user: {user}")
        images = get_user_images(user)
        
        if images:
            print(f"✅ Found {len(images)} images for {user}:")
            for img in images:
                path_exists = os.path.exists(img["path"])
                print(f"  - {img['type']} ({img['format']}): {img['path']} - Exists: {path_exists}")
        else:
            print(f"❌ No images found for {user}")

def test_delete_user_image_specific():
    """Test deleting a specific user image with backup and restore"""
    print("\n=== Testing delete_user_image for specific image ===")
    
    # Choose a test user with multiple images
    test_user = "dimas"  # Assuming this user has multiple images
    test_pose = "left"
    
    # Get original images
    print(f"\nGetting original images for {test_user}")
    original_images = get_user_images(test_user)
    
    if not original_images:
        print(f"❌ No images found for test user {test_user}, skipping test")
        return
    
    # Find the test pose image
    test_image = None
    for img in original_images:
        if img["type"] == test_pose:
            test_image = img
            break
    
    if not test_image:
        print(f"❌ No {test_pose} image found for {test_user}, skipping test")
        return
    
    # Backup the image first
    backup_path = test_image["path"] + ".backup"
    try:
        print(f"Creating backup of {test_image['path']} to {backup_path}")
        import shutil
        shutil.copy2(test_image["path"], backup_path)
        
        # Delete the specific image
        print(f"Attempting to delete {test_pose} image for {test_user}")
        success, message = delete_user_image(test_user, test_pose)
        
        if success:
            print(f"✅ {message}")
            
            # Verify image is gone
            updated_images = get_user_images(test_user)
            still_exists = any(img["type"] == test_pose for img in updated_images)
            
            if not still_exists:
                print(f"✅ Verified {test_pose} image was deleted")
            else:
                print(f"❌ {test_pose} image still exists after deletion")
        else:
            print(f"❌ Failed to delete: {message}")
    
    finally:
        # Restore from backup
        if os.path.exists(backup_path):
            print(f"Restoring {test_image['path']} from backup")
            try:
                shutil.copy2(backup_path, test_image["path"])
                os.remove(backup_path)
                print("✅ Successfully restored image from backup")
            except Exception as e:
                print(f"❌ Failed to restore from backup: {e}")

def run_all_tests():
    """Run all test functions"""
    test_get_user_images()
    test_delete_user_image_specific()
    
    print("\n=== All tests completed ===")

if __name__ == "__main__":
    run_all_tests()
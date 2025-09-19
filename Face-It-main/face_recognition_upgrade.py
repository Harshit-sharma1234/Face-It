#!/usr/bin/env python3
"""
Face Recognition Module Upgrade Script
Seamlessly upgrades the existing face recognition system with enhanced capabilities
"""

import os
import shutil
import sys
from datetime import datetime

def backup_original_module():
    """Create a backup of the original face recognition module"""
    original_file = "face_recognition_module.py"
    backup_file = f"face_recognition_module_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    
    if os.path.exists(original_file):
        shutil.copy2(original_file, backup_file)
        print(f"✓ Backed up original module to: {backup_file}")
        return True
    else:
        print("⚠ Original face_recognition_module.py not found")
        return False

def update_main_application():
    """Update main application files to use the enhanced module"""
    
    # Files that might import the face recognition module
    files_to_update = [
        "main_gui.py",
        "attendance_tracker.py"
    ]
    
    for filename in files_to_update:
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace imports
                updated_content = content.replace(
                    "from face_recognition_module import FaceRecognitionModule",
                    "from enhanced_face_recognition_module import EnhancedFaceRecognitionModule as FaceRecognitionModule"
                )
                
                updated_content = updated_content.replace(
                    "import face_recognition_module",
                    "import enhanced_face_recognition_module as face_recognition_module"
                )
                
                # Only write if changes were made
                if updated_content != content:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    print(f"✓ Updated imports in: {filename}")
                else:
                    print(f"ℹ No changes needed in: {filename}")
                    
            except Exception as e:
                print(f"✗ Error updating {filename}: {e}")
        else:
            print(f"ℹ File not found: {filename}")

def create_compatibility_wrapper():
    """Create a compatibility wrapper for seamless integration"""
    wrapper_content = '''"""
Compatibility wrapper for enhanced face recognition module
This ensures backward compatibility with existing code
"""

from enhanced_face_recognition_module import EnhancedFaceRecognitionModule

# Create an alias for backward compatibility
FaceRecognitionModule = EnhancedFaceRecognitionModule

# Export the class for direct import
__all__ = ['FaceRecognitionModule', 'EnhancedFaceRecognitionModule']
'''
    
    with open("face_recognition_module.py", 'w', encoding='utf-8') as f:
        f.write(wrapper_content)
    
    print("✓ Created compatibility wrapper")

def verify_installation():
    """Verify that the enhanced module can be imported and used"""
    try:
        from enhanced_face_recognition_module import EnhancedFaceRecognitionModule
        
        # Test basic initialization
        module = EnhancedFaceRecognitionModule()
        
        # Test that key methods exist
        required_methods = [
            'load_known_faces',
            'process_frame',
            'get_attendance_updates',
            'reset_tracking',
            'add_new_face'
        ]
        
        for method in required_methods:
            if not hasattr(module, method):
                print(f"✗ Missing required method: {method}")
                return False
        
        print("✓ Enhanced face recognition module verified successfully")
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import enhanced module: {e}")
        return False
    except Exception as e:
        print(f"✗ Error during verification: {e}")
        return False

def main():
    """Main upgrade process"""
    print("🚀 Starting Face Recognition Module Upgrade")
    print("=" * 50)
    
    # Step 1: Backup original module
    print("\n1. Backing up original module...")
    backup_success = backup_original_module()
    
    # Step 2: Create compatibility wrapper
    print("\n2. Creating compatibility wrapper...")
    create_compatibility_wrapper()
    
    # Step 3: Update main application files
    print("\n3. Updating application imports...")
    update_main_application()
    
    # Step 4: Verify installation
    print("\n4. Verifying installation...")
    if verify_installation():
        print("\n✅ Upgrade completed successfully!")
        print("\nEnhanced Features Added:")
        print("• Adaptive lighting compensation")
        print("• Multiple detection models (HOG + CNN)")
        print("• Dynamic tolerance adjustment")
        print("• Face quality assessment")
        print("• Temporal smoothing for stability")
        print("• Performance monitoring and optimization")
        print("• Enhanced noise reduction")
        print("• Improved tracking algorithms")
        
        print("\n📊 The system will now automatically:")
        print("• Adjust to different lighting conditions")
        print("• Switch between detection models for optimal performance")
        print("• Filter out low-quality face detections")
        print("• Provide more stable attendance tracking")
        
    else:
        print("\n❌ Upgrade failed during verification")
        print("Please check the error messages above")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

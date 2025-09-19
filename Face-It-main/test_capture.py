#!/usr/bin/env python3
"""
Test script for the capture photo functionality
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from camera_module import CameraModule
from face_recognition_module_simple import SimpleFaceRecognitionModule
from student_management import StudentManagement
from database import AttendanceDatabase

def test_capture_photo():
    """Test the capture photo functionality"""
    print("Testing capture photo functionality...")
    
    # Create root window
    root = tk.Tk()
    root.title("Test Capture Photo")
    root.geometry("400x300")
    
    # Initialize modules
    database = AttendanceDatabase()
    face_recognition_module = SimpleFaceRecognitionModule()
    camera_module = CameraModule()
    student_management = StudentManagement(database, face_recognition_module)
    
    def start_camera():
        """Start camera for testing"""
        if camera_module.start_camera():
            print("Camera started successfully")
            status_label.config(text="Camera: Active")
            capture_btn.config(state=tk.NORMAL)
        else:
            print("Failed to start camera")
            messagebox.showerror("Error", "Failed to start camera")
    
    def test_capture():
        """Test capture photo"""
        print("Testing capture photo...")
        try:
            photos = student_management.capture_student_photo(camera_module)
            if photos:
                print(f"Successfully captured {len(photos)} photos")
                messagebox.showinfo("Success", f"Captured {len(photos)} photos successfully!")
            else:
                print("No photos captured")
                messagebox.showwarning("Warning", "No photos captured")
        except Exception as e:
            print(f"Error during capture: {e}")
            messagebox.showerror("Error", f"Capture failed: {str(e)}")
    
    def cleanup():
        """Cleanup resources"""
        camera_module.stop_camera()
        root.destroy()
    
    # UI
    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    title_label = ttk.Label(main_frame, text="Test Capture Photo", font=('Arial', 16, 'bold'))
    title_label.pack(pady=(0, 20))
    
    start_btn = ttk.Button(main_frame, text="Start Camera", command=start_camera)
    start_btn.pack(pady=10)
    
    capture_btn = ttk.Button(main_frame, text="Test Capture Photo", command=test_capture, state=tk.DISABLED)
    capture_btn.pack(pady=10)
    
    status_label = ttk.Label(main_frame, text="Camera: Not Active")
    status_label.pack(pady=10)
    
    close_btn = ttk.Button(main_frame, text="Close", command=cleanup)
    close_btn.pack(pady=10)
    
    # Handle window close
    root.protocol("WM_DELETE_WINDOW", cleanup)
    
    print("Test window created. Click 'Start Camera' then 'Test Capture Photo'")
    root.mainloop()

if __name__ == "__main__":
    test_capture_photo()


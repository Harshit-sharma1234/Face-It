import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import time
from typing import List, Optional, Callable

class CameraPreviewWindow:
    def __init__(self, parent, camera_module, face_recognition_module):
        self.parent = parent
        self.camera_module = camera_module
        self.face_recognition_module = face_recognition_module
        
        # Window setup
        self.window = tk.Toplevel(parent)
        self.window.title("Capture Student Photo")
        self.window.geometry("800x700")
        self.window.configure(bg='#f0f0f0')
        self.window.resizable(True, True)
        
        # Center the window
        if parent:
            self.window.transient(parent)
            self.window.grab_set()
        
        # Set up window close handler
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Variables
        self.is_capturing = False
        self.captured_images = []
        self.current_frame = None
        self.update_interval = 50  # milliseconds
        
        # Setup UI
        self.setup_ui()
        
        # Start camera preview
        self.start_preview()
        
        # Start update loop
        self.update_preview()
        
        # Force window to update and show all widgets
        self.window.update_idletasks()
        self.window.update()
    
    def setup_ui(self):
        """Setup the camera preview interface"""
        # Main container
        main_frame = tk.Frame(self.window, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_frame, text="📸 Capture Student Photo", 
                              font=('Arial', 16, 'bold'), bg='#f0f0f0')
        title_label.pack(pady=(0, 10))
        
        # Instructions
        instructions = tk.Label(main_frame, 
                               text="Position your face in the camera view and click 'Capture Photo' to take multiple shots from different angles",
                               font=('Arial', 10), wraplength=700, bg='#f0f0f0')
        instructions.pack(pady=(0, 10))
        
        # Camera preview frame
        preview_frame = tk.LabelFrame(main_frame, text="Camera Preview", bg='#f0f0f0')
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Camera canvas
        self.camera_canvas = tk.Canvas(preview_frame, bg='black', width=640, height=480)
        self.camera_canvas.pack(pady=10)
        
        # Control buttons - make them very prominent
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(fill=tk.X, pady=10)
        
        # Create buttons with pack layout - using regular tkinter buttons
        self.capture_btn = tk.Button(button_frame, text="📸 Capture Photo", 
                                    command=self.capture_photo, 
                                    bg='#0078d4', fg='white', font=('Arial', 12, 'bold'),
                                    padx=30, pady=10, relief=tk.RAISED, bd=3)
        self.capture_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.clear_btn = tk.Button(button_frame, text="🗑️ Clear All", 
                                  command=self.clear_captures,
                                  bg='#ff6b35', fg='white', font=('Arial', 12, 'bold'),
                                  padx=30, pady=10, relief=tk.RAISED, bd=3)
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.finish_btn = tk.Button(button_frame, text="✅ Finish & Add Student", 
                                   command=self.finish_capture,
                                   bg='#28a745', fg='white', font=('Arial', 12, 'bold'),
                                   padx=30, pady=10, relief=tk.RAISED, bd=3)
        self.finish_btn.pack(side=tk.RIGHT)
        
        # Status label
        self.status_label = tk.Label(main_frame, text="Ready to capture photos", 
                                    font=('Arial', 10, 'italic'), bg='#f0f0f0')
        self.status_label.pack(pady=(10, 0))
        
        # Captured photos display (simplified)
        photos_frame = tk.LabelFrame(main_frame, text="Captured Photos", bg='#f0f0f0')
        photos_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Simple frame for photos
        self.scrollable_frame = tk.Frame(photos_frame, bg='#f0f0f0', height=100)
        self.scrollable_frame.pack(fill=tk.X, padx=10, pady=10)
    
    def configure_styles(self):
        """Configure custom button styles - minimal design"""
        style = ttk.Style()
        
        # Minimal button styles
        style.configure('Primary.TButton', font=('Arial', 10, 'bold'), padding=[10, 5])
        style.configure('Success.TButton', font=('Arial', 10, 'bold'), padding=[10, 5])
        style.configure('Warning.TButton', font=('Arial', 10, 'bold'), padding=[10, 5])
    
    def start_preview(self):
        """Start camera preview"""
        print("Starting camera preview...")
        if not self.camera_module.is_camera_active():
            print("Camera is not active!")
            messagebox.showerror("Error", "Camera is not active. Please start the camera first.")
            self.window.destroy()
            return
        
        print("Camera is active, starting preview...")
        # Store the original callback
        self.original_callback = self.camera_module.callback
        # Set our callback
        self.camera_module.set_callback(self.process_frame)
        self.is_capturing = True
        print("Camera preview started successfully")
    
    def process_frame(self, frame):
        """Process camera frame for preview"""
        if self.is_capturing:
            # Detect faces in the frame
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_recognition_module.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
            
            # Draw face rectangles
            frame_with_faces = frame.copy()
            for (x, y, w, h) in faces:
                cv2.rectangle(frame_with_faces, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame_with_faces, "Face Detected", (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            self.current_frame = frame_with_faces
    
    def update_preview(self):
        """Update the camera preview"""
        try:
            if self.current_frame is not None and self.is_capturing:
                # Convert frame to PIL Image
                frame_rgb = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                
                # Resize to fit canvas
                canvas_width = self.camera_canvas.winfo_width()
                canvas_height = self.camera_canvas.winfo_height()
                
                if canvas_width > 1 and canvas_height > 1:
                    pil_image = pil_image.resize((canvas_width, canvas_height), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(pil_image)
                    
                    # Update canvas
                    self.camera_canvas.delete("all")
                    self.camera_canvas.create_image(canvas_width//2, canvas_height//2, image=photo)
                    self.camera_canvas.image = photo  # Keep a reference
        except Exception as e:
            print(f"Error updating preview: {e}")
        
        # Schedule next update
        if self.is_capturing:
            self.window.after(self.update_interval, self.update_preview)
    
    def capture_photo(self):
        """Capture a photo"""
        print("Capture photo button clicked")
        if self.current_frame is None:
            print("No camera feed available")
            messagebox.showwarning("Warning", "No camera feed available")
            return
        
        print("Processing frame for face detection...")
        # Detect faces in current frame
        gray = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_recognition_module.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
        
        print(f"Detected {len(faces)} faces")
        if len(faces) == 0:
            messagebox.showwarning("Warning", "No face detected in the current frame. Please position your face in the camera view.")
            return
        elif len(faces) > 1:
            messagebox.showwarning("Warning", "Multiple faces detected. Please ensure only one face is visible.")
            return
        
        # Add the captured image
        self.captured_images.append(self.current_frame.copy())
        print(f"Photo captured! Total photos: {len(self.captured_images)}")
        
        # Update status
        self.status_label.config(text=f"Captured {len(self.captured_images)} photo(s). Take more from different angles for better recognition.")
        
        # Add thumbnail to scrollable frame
        self.add_photo_thumbnail(self.current_frame, len(self.captured_images))
        
        # Flash effect
        self.flash_effect()
    
    def add_photo_thumbnail(self, image, photo_num):
        """Add a thumbnail to the captured photos display"""
        # Create thumbnail
        thumbnail = cv2.resize(image, (100, 75))
        thumbnail_rgb = cv2.cvtColor(thumbnail, cv2.COLOR_BGR2RGB)
        pil_thumbnail = Image.fromarray(thumbnail_rgb)
        photo_thumbnail = ImageTk.PhotoImage(pil_thumbnail)
        
        # Create thumbnail frame
        thumb_frame = ttk.Frame(self.scrollable_frame)
        thumb_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Thumbnail label
        thumb_label = ttk.Label(thumb_frame, image=photo_thumbnail)
        thumb_label.image = photo_thumbnail  # Keep reference
        thumb_label.pack()
        
        # Photo number label
        num_label = ttk.Label(thumb_frame, text=f"Photo {photo_num}", font=('Arial', 8))
        num_label.pack()
    
    def flash_effect(self):
        """Create a flash effect when capturing"""
        original_bg = self.camera_canvas['bg']
        self.camera_canvas.configure(bg='white')
        self.window.after(100, lambda: self.camera_canvas.configure(bg=original_bg))
    
    def clear_captures(self):
        """Clear all captured photos"""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all captured photos?"):
            self.captured_images.clear()
            
            # Clear thumbnails
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            
            self.status_label.config(text="Ready to capture photos")
    
    def finish_capture(self):
        """Finish capturing and return the images"""
        if len(self.captured_images) == 0:
            messagebox.showwarning("Warning", "No photos captured. Please capture at least one photo.")
            return
        
        print("Finishing capture...")
        # Stop capturing
        self.is_capturing = False
        
        # Restore original callback
        if hasattr(self, 'original_callback'):
            self.camera_module.set_callback(self.original_callback)
        
        # Return the captured images
        self.window.result = self.captured_images
        self.window.destroy()
    
    def on_closing(self):
        """Handle window closing"""
        print("Camera preview window closing...")
        self.is_capturing = False
        # Restore original callback
        if hasattr(self, 'original_callback'):
            self.camera_module.set_callback(self.original_callback)
        # Set empty result if no photos were captured
        if not hasattr(self.window, 'result'):
            self.window.result = []
        self.window.destroy()

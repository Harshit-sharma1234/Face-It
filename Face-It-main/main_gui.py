import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import time
from datetime import datetime, date
import os

# Import our custom modules
from database import AttendanceDatabase
try:
    from enhanced_face_recognition_module import EnhancedFaceRecognitionModule as FaceRecognitionModule
except ImportError:
    from face_recognition_module_simple import SimpleFaceRecognitionModule as FaceRecognitionModule
from camera_module import CameraModule
from student_management import StudentManagement
from attendance_tracker import AttendanceTracker

class FacialAttendanceSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Face-It: Advanced Facial Attendance System")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f8f9fa')
        
        # Configure modern styling
        self.configure_styles()
        
        # Reduce OpenCV log noise
        try:
            cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
        except Exception:
            pass
        
        # Initialize modules
        self.database = AttendanceDatabase()
        self.face_recognition_module = FaceRecognitionModule()
        self.camera_module = CameraModule()
        self.student_management = StudentManagement(self.database, self.face_recognition_module)
        self.attendance_tracker = AttendanceTracker(self.database, self.face_recognition_module)
        
        # Load known faces
        self.load_known_faces()
        
        # Variables
        self.is_camera_active = False
        self.is_tracking_active = False
        self.current_frame = None
        self.update_interval = 100  # milliseconds
        
        # Setup UI
        self.setup_ui()
        
        # Start update loop
        self.update_ui()
    
    def configure_styles(self):
        """Configure professional modern styling for the application"""
        style = ttk.Style()
        
        # Professional Dark Theme Palette
        self.bg_color = '#0F111A'      # Deep Deep Navy/Black
        self.sidebar_color = '#161925' # Sidebar background
        self.accent_color = '#007AFF'  # iOS/Professional Blue
        self.surface_color = '#1C1C26' # Card/Header Surface
        self.text_color = '#FFFFFF'    # White
        self.muted_text = '#9499B0'    # Muted Blue-Grey
        self.success_color = '#34C759'
        self.warning_color = '#FF9F0A'
        self.danger_color = '#FF3B30'
        self.border_color = '#2A2D3E'
        
        # Modern Font Stack
        self.font_family = "Inter" if "Inter" in self.root.tk.call('font', 'families') else "Segoe UI"
        self.header_font = (self.font_family, 12, 'bold')
        self.title_font = (self.font_family, 24, 'bold')
        self.body_font = (self.font_family, 10)
        self.small_font = (self.font_family, 9)
        
        # Configure notebook style (though we'll move to sidebar, keeping styles for compat)
        style.configure('TNotebook', background=self.bg_color, borderwidth=0)
        style.configure('TNotebook.Tab', padding=[20, 10], font=self.body_font)
        
        # Configure frame styles
        style.configure('TFrame', background=self.bg_color)
        style.configure('Sidebar.TFrame', background=self.sidebar_color)
        style.configure('Card.TFrame', background=self.surface_color, relief='flat')
        style.configure('Header.TFrame', background=self.surface_color, relief='flat')
        
        # Configure label styles
        style.configure('TLabel', background=self.bg_color, foreground=self.text_color, font=self.body_font)
        style.configure('Sidebar.TLabel', background=self.sidebar_color, foreground=self.text_color, font=self.body_font)
        style.configure('Title.TLabel', font=self.title_font, background=self.bg_color, foreground=self.text_color)
        style.configure('Subtitle.TLabel', font=(self.font_family, 14), background=self.bg_color, foreground=self.accent_color)
        style.configure('Header.TLabel', font=self.header_font, background=self.surface_color, foreground=self.text_color)
        style.configure('Muted.TLabel', font=self.small_font, background=self.bg_color, foreground=self.muted_text)
        
        # Configure button styles
        style.configure('TButton', font=self.body_font, padding=[15, 8])
        style.configure('Sidebar.TButton', font=self.body_font, padding=[20, 12], width=20)
        
        # Treeview styling - Professional look
        style.configure('Treeview', 
                        font=self.body_font, 
                        rowheight=40, 
                        background=self.surface_color, 
                        fieldbackground=self.surface_color, 
                        foreground=self.text_color,
                        borderwidth=0)
        style.configure('Treeview.Heading', 
                        font=self.header_font, 
                        background=self.border_color, 
                        foreground=self.text_color,
                        relief='flat')
        style.map('Treeview', background=[('selected', self.accent_color)])
        
        # Configure labelframe
        style.configure('TLabelframe', background=self.surface_color, bordercolor=self.border_color, borderwidth=1)
        style.configure('TLabelframe.Label', font=self.header_font, background=self.surface_color, foreground=self.accent_color)
    
    def load_known_faces(self):
        """Load known faces from database"""
        students = self.database.get_all_students()
        self.face_recognition_module.load_known_faces(students)
    
    def setup_ui(self):
        """Setup the main user interface with a professional sidebar layout"""
        # Create main container
        self.main_container = tk.Frame(self.root, bg=self.bg_color)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # 1. Sidebar Frame
        self.sidebar = tk.Frame(self.main_container, bg=self.sidebar_color, width=280)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        
        # Sidebar Content
        logo_frame = tk.Frame(self.sidebar, bg=self.sidebar_color)
        logo_frame.pack(pady=(40, 30), padx=20, fill=tk.X)
        
        tk.Label(logo_frame, text="Face-It", font=self.title_font, 
                 bg=self.sidebar_color, fg=self.text_color).pack(anchor="w")
        tk.Label(logo_frame, text="AI Attendance System", font=self.small_font, 
                 bg=self.sidebar_color, fg=self.accent_color).pack(anchor="w")
        
        # Navigation Buttons
        self.nav_buttons = {}
        nav_items = [
            ("Dashboard", "□"),
            ("Camera View", "○"),
            ("Students", "⊞"),
            ("Attendance", "▤"),
            ("Reports", "")
        ]
        
        nav_container = tk.Frame(self.sidebar, bg=self.sidebar_color)
        nav_container.pack(fill=tk.X, padx=10)
        
        for text, icon in nav_items:
            # We'll use simple text for now, but style it nicely
            btn = tk.Button(nav_container, text=f"  {text}", font=self.body_font,
                           bg=self.sidebar_color, fg=self.muted_text,
                           activebackground=self.accent_color, activeforeground="white",
                           bd=0, padx=20, pady=15, anchor="w",
                           relief='flat', cursor="hand2",
                           command=lambda t=text: self.switch_tab(t))
            btn.pack(fill=tk.X, pady=2)
            self.nav_buttons[text] = btn
            
        # 2. Main Content Area
        self.main_content = tk.Frame(self.main_container, bg=self.bg_color)
        self.main_content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Header Area
        self.header_frame = tk.Frame(self.main_content, bg=self.surface_color, height=80)
        self.header_frame.pack(side=tk.TOP, fill=tk.X)
        self.header_frame.pack_propagate(False)
        
        self.header_title = tk.Label(self.header_frame, text="Dashboard", font=self.header_font,
                                    bg=self.surface_color, fg=self.text_color)
        self.header_title.pack(side=tk.LEFT, padx=30, pady=25)
        
        # Content Container
        self.content_container = tk.Frame(self.main_content, bg=self.bg_color, padx=30, pady=30)
        self.content_container.pack(fill=tk.BOTH, expand=True)
        
        # Initialize tabs dictionary
        self.tabs = {}
        
        # Create all tabs
        self.tabs["Dashboard"] = self.create_dashboard_tab()
        self.tabs["Camera View"] = self.create_camera_tab()
        self.tabs["Students"] = self.create_students_tab()
        self.tabs["Attendance"] = self.create_attendance_tab()
        self.tabs["Reports"] = self.create_reports_tab()
        
        # Show initial tab
        self.switch_tab("Dashboard")
        
        # Populate camera list on startup
        try:
            self.refresh_cameras()
        except Exception as e:
            print(f"Error refreshing cameras on startup: {e}")
        
        # Status bar - refined for bottom
        self.status_bar = tk.Label(self.main_content, text="Ready", font=self.small_font,
                                  bg=self.bg_color, fg=self.muted_text, 
                                  anchor=tk.W, padx=30, pady=10)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def switch_tab(self, tab_name):
        """Switch between different navigation tabs"""
        # Update header title
        if hasattr(self, 'header_title'):
            self.header_title.config(text=tab_name)
            
        # Update button highlights
        for name, btn in self.nav_buttons.items():
            if name == tab_name:
                btn.config(fg=self.accent_color, font=(self.font_family, 10, 'bold'))
            else:
                btn.config(fg=self.muted_text, font=self.body_font)
                
        # Hide all tab frames
        for tab in self.tabs.values():
            tab.pack_forget()
            
        # Show the selected tab frame
        self.tabs[tab_name].pack(fill=tk.BOTH, expand=True)
    
    def create_dashboard_tab(self):
        """Create the main dashboard tab with professional cards"""
        dashboard_frame = tk.Frame(self.content_container, bg=self.bg_color)
        
        # 1. Stats Cards Row
        stats_container = tk.Frame(dashboard_frame, bg=self.bg_color)
        stats_container.pack(fill=tk.X, pady=(0, 20))
        
        def create_stat_card(parent, title, value_attr, icon_text, color):
            card = tk.Frame(parent, bg=self.surface_color, padx=20, pady=20, 
                           highlightthickness=1, highlightbackground=self.border_color)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            tk.Label(card, text=icon_text, font=(self.font_family, 20), bg=self.surface_color, fg=color).pack(anchor="w")
            tk.Label(card, text=title, font=self.small_font, bg=self.surface_color, fg=self.muted_text).pack(anchor="w", pady=(5, 0))
            val_label = tk.Label(card, text="0", font=(self.font_family, 22, 'bold'), bg=self.surface_color, fg=self.text_color)
            val_label.pack(anchor="w")
            setattr(self, value_attr, val_label)
            return card

        create_stat_card(stats_container, "Total Enrolled", "total_students_label", "👥", self.accent_color)
        create_stat_card(stats_container, "Checked In", "present_today_label", "✓", self.success_color)
        create_stat_card(stats_container, "Attendance", "attendance_percent_label", "📈", self.warning_color)
        create_stat_card(stats_container, "Active Session", "total_entries_label", "⏱", self.accent_color)

        # 2. Session Info Card
        session_card = tk.Frame(dashboard_frame, bg=self.surface_color, padx=25, pady=20,
                               highlightthickness=1, highlightbackground=self.border_color)
        session_card.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(session_card, text="Live Session Analytics", font=self.header_font, bg=self.surface_color, fg=self.text_color).pack(side=tk.LEFT)
        
        details_frame = tk.Frame(session_card, bg=self.surface_color)
        details_frame.pack(side=tk.RIGHT)
        
        # In Building
        tk.Label(details_frame, text="Current In-Building: ", font=self.small_font, bg=self.surface_color, fg=self.muted_text).pack(side=tk.LEFT, padx=(20, 0))
        self.current_present_label = tk.Label(details_frame, text="0", font=self.header_font, bg=self.surface_color, fg=self.success_color)
        self.current_present_label.pack(side=tk.LEFT)
        
        # Duration
        tk.Label(details_frame, text="Session Duration: ", font=self.small_font, bg=self.surface_color, fg=self.muted_text).pack(side=tk.LEFT, padx=(20, 0))
        self.session_duration_label = tk.Label(details_frame, text="00:00:00", font=self.header_font, bg=self.surface_color, fg=self.text_color)
        self.session_duration_label.pack(side=tk.LEFT)
        
        # Exits
        tk.Label(details_frame, text="Total Exits: ", font=self.small_font, bg=self.surface_color, fg=self.muted_text).pack(side=tk.LEFT, padx=(20, 0))
        self.total_exits_label = tk.Label(details_frame, text="0", font=self.header_font, bg=self.surface_color, fg=self.danger_color)
        self.total_exits_label.pack(side=tk.LEFT)

        # 3. Controls Row
        bottom_container = tk.Frame(dashboard_frame, bg=self.bg_color)
        bottom_container.pack(fill=tk.BOTH, expand=True)
        
        # Camera Control Card
        cam_card = tk.LabelFrame(bottom_container, text=" Camera System ", font=self.header_font,
                                bg=self.bg_color, fg=self.accent_color, padx=15, pady=15)
        cam_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.start_camera_btn = ttk.Button(cam_card, text="Start Camera", 
                                          style='Success.TButton', command=self.start_camera)
        self.start_camera_btn.pack(fill=tk.X, pady=5)
        
        self.stop_camera_btn = ttk.Button(cam_card, text="Stop Camera", 
                                         style='Danger.TButton', command=self.stop_camera, state=tk.DISABLED)
        self.stop_camera_btn.pack(fill=tk.X, pady=5)
        
        self.camera_info_label = tk.Label(cam_card, text="Camera: Not Active", 
                                        font=self.small_font, bg=self.bg_color, fg=self.muted_text)
        self.camera_info_label.pack(pady=5)

        # Tracking Control Card
        track_card = tk.LabelFrame(bottom_container, text=" Attendance Tracking ", font=self.header_font,
                                  bg=self.bg_color, fg=self.accent_color, padx=15, pady=15)
        track_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        self.start_tracking_btn = ttk.Button(track_card, text="Start Tracking", 
                                            command=self.start_tracking, state=tk.DISABLED)
        self.start_tracking_btn.pack(fill=tk.X, pady=5)
        
        self.stop_tracking_btn = ttk.Button(track_card, text="Stop Tracking", 
                                           command=self.stop_tracking, state=tk.DISABLED)
        self.stop_tracking_btn.pack(fill=tk.X, pady=5)
        
        self.reset_session_btn = ttk.Button(track_card, text="Reset Session", 
                                           command=self.reset_session)
        self.reset_session_btn.pack(fill=tk.X, pady=5)
        
        return dashboard_frame
    
    def create_camera_tab(self):
        """Create the camera view tab with an optimized layout"""
        camera_frame = tk.Frame(self.content_container, bg=self.bg_color)
        
        # Camera Feed Card - Centered and Enlarged
        feed_container = tk.Frame(camera_frame, bg=self.bg_color)
        feed_container.pack(fill=tk.BOTH, expand=True)
        
        feed_card = tk.Frame(feed_container, bg=self.surface_color, padx=10, pady=10, 
                            highlightthickness=1, highlightbackground=self.border_color)
        feed_card.place(relx=0.5, rely=0.45, anchor="center")
        
        self.camera_canvas = tk.Canvas(feed_card, bg='black', width=720, height=480, highlightthickness=0)
        self.camera_canvas.pack()
        
        # Control Panel Card at Bottom
        control_card = tk.Frame(camera_frame, bg=self.surface_color, padx=20, pady=15,
                               highlightthickness=1, highlightbackground=self.border_color)
        control_card.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
        
        # Camera Selection
        select_frame = tk.Frame(control_card, bg=self.surface_color)
        select_frame.pack(side=tk.LEFT)
        
        tk.Label(select_frame, text="Active Source:", font=self.small_font, bg=self.surface_color, fg=self.muted_text).pack(side=tk.LEFT, padx=5)
        self.camera_var = tk.StringVar(value="0")
        self.camera_combo = ttk.Combobox(select_frame, textvariable=self.camera_var, width=5, state="readonly")
        self.camera_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(select_frame, text="Refresh List", command=self.refresh_cameras).pack(side=tk.LEFT, padx=10)
        
        # Settings (Right aligned)
        settings_frame = tk.Frame(control_card, bg=self.surface_color)
        settings_frame.pack(side=tk.RIGHT)
        
        tk.Label(settings_frame, text="Res:", font=self.small_font, bg=self.surface_color, fg=self.muted_text).pack(side=tk.LEFT, padx=5)
        self.resolution_var = tk.StringVar(value="640x480")
        ttk.Combobox(settings_frame, textvariable=self.resolution_var, values=["320x240", "640x480", "1280x720"], width=10, state="readonly").pack(side=tk.LEFT, padx=5)
        
        self.apply_settings_btn = ttk.Button(settings_frame, text="Apply Config", style='Primary.TButton', command=self.apply_camera_settings)
        self.apply_settings_btn.pack(side=tk.LEFT, padx=10)
        
        return camera_frame
    
    def create_students_tab(self):
        """Create the students management tab"""
        students_frame = ttk.Frame(self.content_container, padding=20)
        # We don't add to notebook anymore, just return the frame
        
        # Add student section
        add_frame = ttk.LabelFrame(students_frame, text="Add New Student", padding=10)
        add_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Student form
        form_frame = ttk.Frame(add_frame)
        form_frame.pack(fill=tk.X, expand=True)
        
        # Configure grid weights
        form_frame.grid_columnconfigure(0, weight=1)
        form_frame.grid_columnconfigure(1, weight=1)
        form_frame.grid_columnconfigure(2, weight=1)
        form_frame.grid_columnconfigure(3, weight=1)
        
        # Row 1
        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.student_name_var = tk.StringVar()
        self.student_name_entry = ttk.Entry(form_frame, textvariable=self.student_name_var, width=30)
        self.student_name_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(form_frame, text="Student ID:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.student_id_var = tk.StringVar()
        self.student_id_entry = ttk.Entry(form_frame, textvariable=self.student_id_var, width=20)
        self.student_id_entry.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))
        
        # Row 2 - Buttons
        self.capture_photo_btn = ttk.Button(form_frame, text="Capture Photo", 
                                           style='Primary.TButton', command=self.capture_student_photo)
        self.capture_photo_btn.grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        
        self.load_photo_btn = ttk.Button(form_frame, text="Load Photo", 
                                        style='Primary.TButton', command=self.load_student_photo)
        self.load_photo_btn.grid(row=1, column=1, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        
        # Add student button
        self.add_student_btn = ttk.Button(form_frame, text="Add Student", 
                                         style='Success.TButton', command=self.add_student)
        self.add_student_btn.grid(row=2, column=0, columnspan=4, pady=(10, 0))
        
        # Student list section
        list_frame = ttk.LabelFrame(students_frame, text="Student List", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Search frame
        search_frame = ttk.Frame(list_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 10))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        self.search_btn = ttk.Button(search_frame, text="Search", style='Primary.TButton', command=self.search_students)
        self.search_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_search_btn = ttk.Button(search_frame, text="Clear", style='Warning.TButton', command=self.clear_search)
        self.clear_search_btn.pack(side=tk.LEFT)
        
        # Student treeview
        columns = ('ID', 'Name', 'Student ID', 'Status')
        self.student_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.student_tree.heading(col, text=col)
            self.student_tree.column(col, width=150)
        
        # Scrollbar
        student_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.student_tree.yview)
        self.student_tree.configure(yscrollcommand=student_scrollbar.set)
        
        self.student_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        student_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action buttons
        action_frame = ttk.Frame(list_frame)
        action_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.export_students_btn = ttk.Button(action_frame, text="Export Students", 
                                             style='Primary.TButton', command=self.export_students)
        self.export_students_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.delete_student_btn = ttk.Button(action_frame, text="Delete Selected", 
                                            style='Danger.TButton', command=self.delete_selected_student)
        self.delete_student_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.refresh_students_btn = ttk.Button(action_frame, text="Refresh List", 
                                              style='Warning.TButton', command=self.refresh_student_list)
        self.refresh_students_btn.pack(side=tk.LEFT)
        
        # Load initial student list
        self.refresh_student_list()
        return students_frame
    
    def create_attendance_tab(self):
        """Create the attendance tracking tab"""
        attendance_frame = ttk.Frame(self.content_container, padding=20)
        # We don't add to notebook anymore, just return the frame
        
        # Real-time attendance section
        realtime_frame = ttk.LabelFrame(attendance_frame, text="Real-time Attendance", padding=10)
        realtime_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Attendance treeview
        columns = ('ID', 'Name', 'Student ID', 'Status', 'Last Update')
        self.attendance_tree = ttk.Treeview(realtime_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.attendance_tree.heading(col, text=col)
            self.attendance_tree.column(col, width=150)
        
        # Scrollbar
        attendance_scrollbar = ttk.Scrollbar(realtime_frame, orient=tk.VERTICAL, command=self.attendance_tree.yview)
        self.attendance_tree.configure(yscrollcommand=attendance_scrollbar.set)
        
        self.attendance_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        attendance_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Attendance log section
        log_frame = ttk.LabelFrame(attendance_frame, text="Attendance Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Log treeview
        log_columns = ('Timestamp', 'Student', 'Action')
        self.log_tree = ttk.Treeview(log_frame, columns=log_columns, show='headings', height=10)
        
        for col in log_columns:
            self.log_tree.heading(col, text=col)
            self.log_tree.column(col, width=200)
        
        # Log scrollbar
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Log controls
        log_controls_frame = ttk.Frame(log_frame)
        log_controls_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.clear_log_btn = ttk.Button(log_controls_frame, text="Clear Log", 
                                       style='Warning.TButton', command=self.clear_attendance_log)
        self.clear_log_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.export_log_btn = ttk.Button(log_controls_frame, text="Export Log", 
                                        style='Primary.TButton', command=self.export_attendance_log)
        self.export_log_btn.pack(side=tk.LEFT)
        return attendance_frame
    
    def create_reports_tab(self):
        """Create the reports tab"""
        reports_frame = ttk.Frame(self.content_container, padding=20)
        # We don't add to notebook anymore, just return the frame
        
        # Daily summary section
        summary_frame = ttk.LabelFrame(reports_frame, text="Daily Summary", padding=10)
        summary_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Summary display
        summary_display_frame = ttk.Frame(summary_frame)
        summary_display_frame.pack(fill=tk.X)
        
        # Date selection
        ttk.Label(summary_display_frame, text="Date:").pack(side=tk.LEFT, padx=(0, 10))
        self.report_date_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        self.report_date_entry = ttk.Entry(summary_display_frame, textvariable=self.report_date_var, width=15)
        self.report_date_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        self.generate_summary_btn = ttk.Button(summary_display_frame, text="Generate Summary", 
                                             style='Primary.TButton', command=self.generate_daily_summary)
        self.generate_summary_btn.pack(side=tk.LEFT, padx=(0, 20))
        
        self.export_summary_btn = ttk.Button(summary_display_frame, text="Export Summary", 
                                            style='Success.TButton', command=self.export_daily_summary)
        self.export_summary_btn.pack(side=tk.LEFT)
        
        # Summary results
        self.summary_text = tk.Text(summary_frame, height=8, width=80)
        self.summary_text.pack(fill=tk.X, pady=(10, 0))
        
        # Attendance history section
        history_frame = ttk.LabelFrame(reports_frame, text="Attendance History", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Date range selection
        range_frame = ttk.Frame(history_frame)
        range_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(range_frame, text="From:").pack(side=tk.LEFT, padx=(0, 10))
        self.start_date_var = tk.StringVar(value=(date.today().replace(day=1)).strftime("%Y-%m-%d"))
        self.start_date_entry = ttk.Entry(range_frame, textvariable=self.start_date_var, width=15)
        self.start_date_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(range_frame, text="To:").pack(side=tk.LEFT, padx=(0, 10))
        self.end_date_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        self.end_date_entry = ttk.Entry(range_frame, textvariable=self.end_date_var, width=15)
        self.end_date_entry.pack(side=tk.LEFT, padx=(0, 20))
        
        self.generate_history_btn = ttk.Button(range_frame, text="Generate Report", 
                                             style='Primary.TButton', command=self.generate_attendance_history)
        self.generate_history_btn.pack(side=tk.LEFT, padx=(0, 20))
        
        self.export_history_btn = ttk.Button(range_frame, text="Export Report", 
                                            style='Success.TButton', command=self.export_attendance_history)
        self.export_history_btn.pack(side=tk.LEFT)
        
        # History results
        self.history_text = tk.Text(history_frame, height=10, width=80)
        return reports_frame
    
    # Camera control methods
    def start_camera(self):
        """Start the camera"""
        camera_index = int(self.camera_var.get())
        self.camera_module = CameraModule(camera_index)
        
        if self.camera_module.start_camera():
            self.is_camera_active = True
            self.start_camera_btn.config(state=tk.DISABLED)
            self.stop_camera_btn.config(state=tk.NORMAL)
            self.start_tracking_btn.config(state=tk.NORMAL)
            self.camera_info_label.config(text=f"Camera: Active (Index {camera_index})")
            self.status_bar.config(text="Camera started successfully")
            
            # Set camera callback
            self.camera_module.set_callback(self.process_camera_frame)
        else:
            # Offer fallback to video file source
            if messagebox.askyesno("Camera Not Found", "No camera could be opened. Would you like to select a video file as a source?"):
                file_path = filedialog.askopenfilename(title="Select Video File", filetypes=[
                    ("Video files", "*.mp4;*.avi;*.mkv;*.mov;*.wmv"),
                    ("All files", "*.*")
                ])
                if file_path:
                    if self.camera_module.start_with_video_file(file_path):
                        self.is_camera_active = True
                        self.start_camera_btn.config(state=tk.DISABLED)
                        self.stop_camera_btn.config(state=tk.NORMAL)
                        self.start_tracking_btn.config(state=tk.NORMAL)
                        self.camera_info_label.config(text=f"Video: {os.path.basename(file_path)}")
                        self.status_bar.config(text="Video source started successfully")
                        self.camera_module.set_callback(self.process_camera_frame)
                        return
            messagebox.showerror("Error", "Failed to start camera")
    
    def stop_camera(self):
        """Stop the camera"""
        if self.is_tracking_active:
            self.stop_tracking()
        
        self.camera_module.stop_camera()
        self.is_camera_active = False
        self.start_camera_btn.config(state=tk.NORMAL)
        self.stop_camera_btn.config(state=tk.DISABLED)
        self.start_tracking_btn.config(state=tk.DISABLED)
        self.stop_tracking_btn.config(state=tk.DISABLED)
        self.camera_info_label.config(text="Camera: Not Active")
        self.status_bar.config(text="Camera stopped")
        
        # Clear camera view
        self.camera_canvas.delete("all")
    
    def process_camera_frame(self, frame):
        """Process camera frame for face recognition"""
        if self.is_tracking_active:
            # Process frame for face recognition
            processed_frame, face_names, face_locations = self.face_recognition_module.process_frame(frame)
            
            # Draw face rectangles and names
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                # Draw rectangle
                cv2.rectangle(processed_frame, (left, top), (right, bottom), (0, 255, 0), 2)
                
                # Draw name
                cv2.putText(processed_frame, name, (left, top - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
            
            self.current_frame = processed_frame
        else:
            self.current_frame = frame
    
    def refresh_cameras(self):
        """Refresh available camera list"""
        available_cameras = self.camera_module.list_available_cameras()
        self.camera_combo.config(values=available_cameras)
        if available_cameras:
            self.camera_var.set(str(available_cameras[0]))
    
    def apply_camera_settings(self):
        """Apply camera settings"""
        if not self.is_camera_active:
            messagebox.showwarning("Warning", "Camera must be active to apply settings")
            return
        
        # Parse resolution
        width, height = map(int, self.resolution_var.get().split('x'))
        fps = int(self.fps_var.get())
        
        self.camera_module.set_camera_properties(width, height, fps)
        messagebox.showinfo("Success", "Camera settings applied")
    
    # Attendance tracking methods
    def start_tracking(self):
        """Start attendance tracking"""
        if not self.is_camera_active:
            messagebox.showwarning("Warning", "Camera must be active to start tracking")
            return
        
        if self.attendance_tracker.start_tracking():
            self.is_tracking_active = True
            self.start_tracking_btn.config(state=tk.DISABLED)
            self.stop_tracking_btn.config(state=tk.NORMAL)
            self.status_bar.config(text="Attendance tracking started")
        else:
            messagebox.showerror("Error", "Failed to start attendance tracking")
    
    def stop_tracking(self):
        """Stop attendance tracking"""
        if self.attendance_tracker.stop_tracking():
            self.is_tracking_active = False
            self.start_tracking_btn.config(state=tk.NORMAL)
            self.stop_tracking_btn.config(state=tk.DISABLED)
            self.status_bar.config(text="Attendance tracking stopped")
    
    def reset_session(self):
        """Reset the current tracking session"""
        if messagebox.askyesno("Confirm", "Are you sure you want to reset the session?"):
            self.attendance_tracker.reset_session()
            self.status_bar.config(text="Session reset")
    
    # Student management methods
    def capture_student_photo(self):
        """Capture photo for new student"""
        if not self.is_camera_active:
            messagebox.showwarning("Warning", "Camera must be active to capture photo")
            return
        
        try:
            # Set parent for the camera preview window
            self.student_management.parent = self.root
            
            print("Starting photo capture process...")
            photos = self.student_management.capture_student_photo(self.camera_module)
            if photos is not None and len(photos) > 0:
                self.captured_photos = photos
                messagebox.showinfo("Success", f"Captured {len(photos)} photo(s) successfully")
                print(f"Successfully captured {len(photos)} photos")
            else:
                print("No photos were captured")
        except Exception as e:
            print(f"Error in capture_student_photo: {e}")
            messagebox.showerror("Error", f"Failed to capture photos: {str(e)}")
    
    def load_student_photo(self):
        """Load photo from file for new student"""
        file_path = filedialog.askopenfilename(
            title="Select Student Photo",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
        )
        
        if file_path:
            photo = self.student_management.load_student_photo(file_path)
            if photo is not None:
                messagebox.showinfo("Success", "Photo loaded successfully")
    
    def add_student(self):
        """Add new student to the system"""
        name = self.student_name_var.get().strip()
        student_id = self.student_id_var.get().strip()
        
        if not name or not student_id:
            messagebox.showwarning("Warning", "Please enter both name and student ID")
            return
        
        if not self.student_management.validate_student_name(name):
            messagebox.showwarning("Warning", "Invalid student name")
            return
        
        if not self.student_management.validate_student_id(student_id):
            messagebox.showwarning("Warning", "Invalid student ID")
            return
        
        # Check if photos are available
        if not hasattr(self, 'captured_photos') or not self.captured_photos:
            if self.student_management.current_student_image is None:
                messagebox.showwarning("Warning", "Please capture or load a photo first")
                return
            # Use single photo if no multiple photos captured
            photos = [self.student_management.current_student_image]
        else:
            photos = self.captured_photos
        
        if self.student_management.add_student_from_photo(name, student_id, photos):
            # Clear form
            self.student_name_var.set("")
            self.student_id_var.set("")
            self.student_management.current_student_image = None
            if hasattr(self, 'captured_photos'):
                self.captured_photos = None
            
            # Refresh student list
            self.refresh_student_list()
            
            # Reload known faces
            self.load_known_faces()
    
    def search_students(self):
        """Search for students"""
        search_term = self.search_var.get().strip()
        if not search_term:
            self.refresh_student_list()
            return
        
        students = self.student_management.search_student(search_term)
        self.update_student_tree(students)
    
    def clear_search(self):
        """Clear search and show all students"""
        self.search_var.set("")
        self.refresh_student_list()
    
    def refresh_student_list(self):
        """Refresh the student list"""
        students = self.student_management.get_student_list()
        self.update_student_tree(students)
    
    def update_student_tree(self, students):
        """Update the student treeview"""
        # Clear existing items
        for item in self.student_tree.get_children():
            self.student_tree.delete(item)
        
        # Add students
        for student in students:
            status = "Has Photo" if student['face_encoding'] else "No Photo"
            self.student_tree.insert('', 'end', values=(
                student['id'],
                student['name'],
                student['student_id'],
                status
            ))
    
    def delete_selected_student(self):
        """Delete the selected student"""
        selected_item = self.student_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a student to delete")
            return
        
        # Get student ID from selected item
        item_values = self.student_tree.item(selected_item[0])['values']
        student_id = int(item_values[0])  # First column is ID
        
        # Delete the student
        if self.student_management.delete_student(student_id):
            # Refresh the student list
            self.refresh_student_list()
            # Reload known faces
            self.load_known_faces()
            self.status_bar.config(text=f"Student deleted successfully")

    def export_students(self):
        """Export student data"""
        file_path = filedialog.asksaveasfilename(
            title="Export Students",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        
        if file_path:
            if self.student_management.export_student_data(file_path):
                self.status_bar.config(text=f"Students exported to {file_path}")
    
    # Attendance methods
    def update_attendance_display(self):
        """Update the attendance display"""
        if not self.is_tracking_active:
            return
        
        # Get real-time updates
        updates = self.attendance_tracker.get_realtime_updates()
        
        # Clear existing items
        for item in self.attendance_tree.get_children():
            self.attendance_tree.delete(item)
        
        # Add current status
        for update in updates:
            self.attendance_tree.insert('', 'end', values=(
                update['id'],
                update['name'],
                update['student_id'],
                update['status'],
                datetime.now().strftime("%H:%M:%S")
            ))
    
    def update_attendance_log(self):
        """Update the attendance log display"""
        if not self.is_tracking_active:
            return
        
        # Get recent log entries
        log_entries = self.attendance_tracker.get_attendance_log(50)
        
        # Clear existing items
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
        
        # Add log entries
        for entry in log_entries:
            self.log_tree.insert('', 'end', values=(
                entry['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                entry['name'],
                entry['action']
            ))
    
    def clear_attendance_log(self):
        """Clear the attendance log display"""
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
    
    def export_attendance_log(self):
        """Export attendance log"""
        file_path = filedialog.asksaveasfilename(
            title="Export Attendance Log",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("Timestamp,Student,Action\n")
                    for item in self.log_tree.get_children():
                        values = self.log_tree.item(item)['values']
                        f.write(f"{values[0]},{values[1]},{values[2]}\n")
                
                messagebox.showinfo("Success", f"Attendance log exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export log: {str(e)}")
    
    # Report methods
    def generate_daily_summary(self):
        """Generate daily summary report"""
        try:
            target_date = datetime.strptime(self.report_date_var.get(), "%Y-%m-%d").date()
            summary = self.attendance_tracker.get_daily_summary(target_date)
            
            summary_text = f"""
Daily Attendance Summary for {summary['date']}

Total Students: {summary['total_students']}
Present: {summary['present_count']}
Absent: {summary['absent_count']}
Attendance Percentage: {summary['attendance_percentage']:.1f}%

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            self.summary_text.delete(1.0, tk.END)
            self.summary_text.insert(1.0, summary_text)
            
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
    
    def export_daily_summary(self):
        """Export daily summary"""
        file_path = filedialog.asksaveasfilename(
            title="Export Daily Summary",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.summary_text.get(1.0, tk.END))
                messagebox.showinfo("Success", f"Summary exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export summary: {str(e)}")
    
    def generate_attendance_history(self):
        """Generate attendance history report"""
        try:
            start_date = datetime.strptime(self.start_date_var.get(), "%Y-%m-%d").date()
            end_date = datetime.strptime(self.end_date_var.get(), "%Y-%m-%d").date()
            
            if start_date > end_date:
                messagebox.showerror("Error", "Start date must be before end date")
                return
            
            # For now, show a simple message
            history_text = f"""
Attendance History Report
From: {start_date} To: {end_date}

This feature will show detailed attendance history for the selected date range.
Currently showing basic information.

Total Students: {len(self.database.get_all_students())}
Date Range: {end_date - start_date} days

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            self.history_text.delete(1.0, tk.END)
            self.history_text.insert(1.0, history_text)
            
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
    
    def export_attendance_history(self):
        """Export attendance history"""
        file_path = filedialog.asksaveasfilename(
            title="Export Attendance History",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.history_text.get(1.0, tk.END))
                messagebox.showinfo("Success", f"History exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export history: {str(e)}")
    
    # UI update methods
    def update_ui(self):
        """Update the UI elements"""
        try:
            # Update camera view
            if self.current_frame is not None and self.is_camera_active:
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
            
            # Update statistics
            if self.is_tracking_active:
                status = self.attendance_tracker.get_current_attendance_status()
                
                self.total_students_label.config(text=str(status['total_students']))
                self.current_present_label.config(text=str(status['current_present']))
                self.present_today_label.config(text=str(status['present_today']))
                self.attendance_percent_label.config(text=f"{status['attendance_percentage']:.1f}%")
                self.session_duration_label.config(text=status['session_duration'])
                self.total_entries_label.config(text=str(status['total_entries_session']))
                self.total_exits_label.config(text=str(status['total_exits_session']))
            
            # Update attendance displays
            if self.is_tracking_active:
                self.update_attendance_display()
                self.update_attendance_log()
            
        except Exception as e:
            print(f"Error updating UI: {e}")
        
        # Schedule next update
        self.root.after(self.update_interval, self.update_ui)

def main():
    """Main function to run the application"""
    root = tk.Tk()
    
    # Set application icon (if available)
    try:
        root.iconbitmap('icon.ico')
    except:
        pass
    
    # Create and run the application
    app = FacialAttendanceSystem(root)
    
    # Handle window close
    def on_closing():
        if app.is_camera_active:
            app.stop_camera()
        if app.is_tracking_active:
            app.stop_tracking()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the main loop
    root.mainloop()

if __name__ == "__main__":
    main()

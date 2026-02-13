import cv2
import numpy as np
import pickle
from typing import List, Tuple, Optional, Dict
import time
import os

class SimpleFaceRecognitionModule:
    def __init__(self):
        # Load OpenCV's pre-trained face detection model
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        self.face_locations = []
        self.face_names = []
        
        # Tracking variables for attendance
        self.present_students = set()  # Set of student IDs currently present
        self.student_tracking = {}  # Track each student's status
        self.entry_threshold = 3  # Frames to confirm entry
        self.exit_threshold = 5   # Frames to confirm exit
        
        # Improved face matching threshold
        self.matching_threshold = 0.4  # Increased threshold for stricter matching
        self.face_size = (128, 128)  # Standardized face size for better matching
        
    def load_known_faces(self, students_data: List[Dict]):
        """Load known faces from database"""
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        
        for student in students_data:
            if student['face_encoding']:
                # Convert bytes back to numpy array
                face_encoding = pickle.loads(student['face_encoding'])
                self.known_face_encodings.append(face_encoding)
                self.known_face_names.append(student['name'])
                self.known_face_ids.append(student['id'])
        
        print(f"Loaded {len(self.known_face_encodings)} known faces")
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, List[str], List[Tuple]]:
        """Process a single frame for face detection"""
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces with improved parameters - more sensitive detection
        faces = self.face_cascade.detectMultiScale(gray, 1.05, 3, minSize=(20, 20))
        
        self.face_locations = []
        self.face_names = []
        
        for (x, y, w, h) in faces:
            # Convert to format expected by the rest of the system
            top, left, bottom, right = y, x, y + h, x + w
            self.face_locations.append((top, right, bottom, left))
            
            # Extract face region
            face_roi = gray[y:y+h, x:x+w]
            
            # Try to match with known faces
            name = "Unknown"
            student_id = None
            
            if len(self.known_face_encodings) > 0:
                face_roi_resized = cv2.resize(face_roi, self.face_size)
                best_match = None
                best_score = 0
                
                for i, known_encoding in enumerate(self.known_face_encodings):
                    if known_encoding.shape != face_roi_resized.shape:
                        known_encoding = cv2.resize(known_encoding, self.face_size)
                    
                    similarity = cv2.matchTemplate(face_roi_resized, known_encoding, cv2.TM_CCOEFF_NORMED)
                    template_score = similarity[0][0]
                    
                    hist1 = cv2.calcHist([face_roi_resized], [0], None, [256], [0, 256])
                    hist2 = cv2.calcHist([known_encoding], [0], None, [256], [0, 256])
                    hist_score = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
                    
                    mse = np.mean((face_roi_resized.astype("float") - known_encoding.astype("float")) ** 2)
                    ssim_score = 1.0 / (1.0 + mse / 10000.0)
                    
                    edges1 = cv2.Canny(face_roi_resized, 50, 150)
                    edges2 = cv2.Canny(known_encoding, 50, 150)
                    edge_similarity = cv2.matchTemplate(edges1, edges2, cv2.TM_CCOEFF_NORMED)
                    edge_score = edge_similarity[0][0] if edge_similarity.size > 0 else 0
                    
                    combined_score = (
                        template_score * 0.3 +
                        hist_score * 0.2 +
                        ssim_score * 0.3 +
                        edge_score * 0.2
                    )
                    
                    if combined_score > best_score and combined_score > self.matching_threshold:
                        best_score = combined_score
                        best_match = i
                
                if best_match is not None:
                    name = self.known_face_names[best_match]
                    student_id = self.known_face_ids[best_match]
                    self.track_student_attendance(student_id, name)
            
            self.face_names.append(name)
        
        return frame, self.face_names, self.face_locations
    
    def track_student_attendance(self, student_id: int, name: str):
        """Track student attendance status"""
        current_time = time.time()
        
        if student_id not in self.student_tracking:
            self.student_tracking[student_id] = {
                'name': name,
                'first_seen': current_time,
                'last_seen': current_time,
                'entry_frames': 0,
                'exit_frames': 0,
                'status': 'unknown'
            }
        else:
            self.student_tracking[student_id]['last_seen'] = current_time
        
        if student_id in self.present_students:
            self.student_tracking[student_id]['entry_frames'] += 1
            self.student_tracking[student_id]['exit_frames'] = 0
        else:
            self.student_tracking[student_id]['entry_frames'] += 1
            self.student_tracking[student_id]['exit_frames'] = 0
            
    def get_attendance_updates(self) -> List[Dict]:
        """Get attendance updates for students"""
        updates = []
        current_time = time.time()
        
        for student_id, tracking in self.student_tracking.items():
            if (tracking['entry_frames'] >= self.entry_threshold and 
                student_id not in self.present_students):
                self.present_students.add(student_id)
                tracking['status'] = 'entered'
                updates.append({
                    'student_id': student_id,
                    'name': tracking['name'],
                    'action': 'entered',
                    'time': current_time
                })
            elif (tracking['exit_frames'] >= self.exit_threshold and 
                  student_id in self.present_students):
                self.present_students.remove(student_id)
                tracking['status'] = 'exited'
                updates.append({
                    'student_id': student_id,
                    'name': tracking['name'],
                    'action': 'exited',
                    'time': current_time
                })
        
        return updates
    
    def get_current_present_students(self) -> List[int]:
        return list(self.present_students)
    
    def get_present_count(self) -> int:
        return len(self.present_students)
    
    def reset_tracking(self):
        self.present_students.clear()
        self.student_tracking.clear()
    
    def add_new_face(self, face_image: np.ndarray, name: str, student_id: int) -> bool:
        try:
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
            if len(faces) > 0:
                x, y, w, h = faces[0]
                face_roi = gray[y:y+h, x:x+w]
                face_encoding = cv2.resize(face_roi, self.face_size)
                face_encoding = cv2.equalizeHist(face_encoding)
                self.known_face_encodings.append(face_encoding)
                self.known_face_names.append(name)
                self.known_face_ids.append(student_id)
                return True
            return False
        except Exception:
            return False

    def add_multiple_face_angles(self, face_images: List[np.ndarray], name: str, student_id: int) -> bool:
        success = False
        for img in face_images:
            if self.add_new_face(img, name, student_id):
                success = True
        return success

    def detect_faces_in_image(self, image: np.ndarray) -> List[Tuple]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        face_locations = []
        for (x, y, w, h) in faces:
            face_locations.append((y, x + w, y + h, x))
        return face_locations
    
    def get_face_encoding(self, image: np.ndarray, face_location: Tuple) -> Optional[np.ndarray]:
        try:
            top, right, bottom, left = face_location
            face_roi = image[top:bottom, left:right]
            gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
            face_encoding = cv2.resize(gray, self.face_size)
            face_encoding = cv2.equalizeHist(face_encoding)
            return face_encoding
        except Exception:
            return None

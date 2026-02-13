import cv2
import face_recognition
import numpy as np
import pickle
from typing import List, Tuple, Optional, Dict
import time
from collections import deque
import logging

class EnhancedFaceRecognitionModule:
    def __init__(self):
        # Core face recognition data
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        
        # Detection results
        self.face_locations = []
        self.face_encodings = []
        self.face_names = []
        
        # Processing optimization
        self.process_this_frame = True
        self.frame_count = 0
        self.detection_interval = 2  # Process every 2nd frame for better performance
        
        # Enhanced detection settings
        self.detection_models = ['hog', 'cnn']  # Multiple models for robustness
        self.current_model = 'hog'  # Start with faster HOG model
        self.model_switch_threshold = 0.3  # Switch to CNN if detection confidence is low
        
        # Adaptive tolerance settings
        self.base_tolerance = 0.6
        self.min_tolerance = 0.4
        self.max_tolerance = 0.8
        self.tolerance_history = deque(maxlen=10)
        
        # Tracking variables for attendance
        self.present_students = set()
        self.student_tracking = {}
        self.entry_threshold = 3
        self.exit_threshold = 8  # Increased for more stable tracking
        
        # Face quality assessment
        self.min_face_size = (50, 50)  # Minimum face size in pixels
        self.face_quality_threshold = 0.7
        
        # Temporal smoothing
        self.detection_history = deque(maxlen=5)  # Store last 5 detections per student
        self.confidence_smoothing = True
        
        # Environmental adaptation
        self.lighting_adaptation = True
        self.contrast_enhancement = True
        self.noise_reduction = True
        
        # Performance monitoring
        self.detection_stats = {
            'total_detections': 0,
            'successful_recognitions': 0,
            'false_positives': 0,
            'model_switches': 0
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """Enhanced preprocessing for different lighting conditions"""
        processed_frame = frame.copy()
        
        # Convert to LAB color space for better lighting handling
        if self.lighting_adaptation:
            lab = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to L channel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            # Merge channels and convert back to BGR
            lab = cv2.merge([l, a, b])
            processed_frame = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # Enhance contrast if needed
        if self.contrast_enhancement:
            # Calculate image brightness
            gray = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            
            # Adjust contrast based on brightness
            if brightness < 100:  # Dark image
                alpha = 1.3  # Contrast control
                beta = 20    # Brightness control
            elif brightness > 180:  # Bright image
                alpha = 0.8
                beta = -10
            else:  # Normal lighting
                alpha = 1.1
                beta = 5
            
            processed_frame = cv2.convertScaleAbs(processed_frame, alpha=alpha, beta=beta)
        
        # Noise reduction
        if self.noise_reduction:
            processed_frame = cv2.bilateralFilter(processed_frame, 9, 75, 75)
        
        return processed_frame
    
    def assess_face_quality(self, face_image: np.ndarray, face_location: Tuple) -> float:
        """Assess the quality of a detected face"""
        top, right, bottom, left = face_location
        face_height = bottom - top
        face_width = right - left
        
        # Check minimum size
        if face_height < self.min_face_size[1] or face_width < self.min_face_size[0]:
            return 0.0
        
        # Calculate sharpness using Laplacian variance
        gray_face = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray_face, cv2.CV_64F).var()
        sharpness_score = min(laplacian_var / 1000.0, 1.0)  # Normalize to 0-1
        
        # Calculate brightness consistency
        brightness_std = np.std(gray_face)
        brightness_score = 1.0 - min(brightness_std / 128.0, 1.0)
        
        # Calculate aspect ratio score (faces should be roughly rectangular)
        aspect_ratio = face_width / face_height
        ideal_ratio = 0.75  # Typical face aspect ratio
        ratio_score = 1.0 - abs(aspect_ratio - ideal_ratio) / ideal_ratio
        
        # Combine scores
        quality_score = (sharpness_score * 0.4 + brightness_score * 0.3 + ratio_score * 0.3)
        
        return quality_score
    
    def adaptive_tolerance_adjustment(self, recent_matches: List[bool]) -> float:
        """Dynamically adjust tolerance based on recent detection performance"""
        if not recent_matches:
            return self.base_tolerance
        
        # Calculate success rate
        success_rate = sum(recent_matches) / len(recent_matches)
        
        # Adjust tolerance based on success rate
        if success_rate < 0.3:  # Too many failures, increase tolerance
            new_tolerance = min(self.base_tolerance + 0.1, self.max_tolerance)
        elif success_rate > 0.8:  # Too many matches, might be false positives
            new_tolerance = max(self.base_tolerance - 0.05, self.min_tolerance)
        else:
            new_tolerance = self.base_tolerance
        
        return new_tolerance
    
    def detect_faces_with_multiple_models(self, rgb_frame: np.ndarray) -> Tuple[List[Tuple], str]:
        """Use multiple detection models for robustness"""
        face_locations = []
        model_used = self.current_model
        
        try:
            # Try current model first
            if self.current_model == 'hog':
                face_locations = face_recognition.face_locations(rgb_frame, model='hog')
            else:
                face_locations = face_recognition.face_locations(rgb_frame, model='cnn')
            
            # If no faces detected or low confidence, try alternative model
            if len(face_locations) == 0 and self.current_model == 'hog':
                try:
                    face_locations = face_recognition.face_locations(rgb_frame, model='cnn')
                    model_used = 'cnn'
                    self.detection_stats['model_switches'] += 1
                except Exception as e:
                    self.logger.warning(f"CNN model failed: {e}")
                    
        except Exception as e:
            self.logger.error(f"Face detection failed with {self.current_model}: {e}")
            # Fallback to basic detection
            try:
                face_locations = face_recognition.face_locations(rgb_frame)
                model_used = 'fallback'
            except Exception:
                face_locations = []
        
        return face_locations, model_used
    
    def smooth_detection_confidence(self, student_id: int, confidence: float) -> float:
        """Apply temporal smoothing to detection confidence"""
        if not self.confidence_smoothing:
            return confidence
        
        # Initialize history for new student
        if student_id not in self.detection_history:
            self.detection_history[student_id] = deque(maxlen=5)
        
        # Add current confidence
        self.detection_history[student_id].append(confidence)
        
        # Calculate smoothed confidence (weighted average)
        history = list(self.detection_history[student_id])
        weights = np.linspace(0.5, 1.0, len(history))  # More weight to recent detections
        
        smoothed_confidence = np.average(history, weights=weights)
        return smoothed_confidence
    
    def load_known_faces(self, students_data: List[Dict]):
        """Load known faces from database with enhanced validation"""
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        
        loaded_count = 0
        for student in students_data:
            if student['face_encoding']:
                try:
                    # Convert bytes back to numpy array
                    face_encoding = pickle.loads(student['face_encoding'])
                    
                    # Validate encoding
                    if isinstance(face_encoding, np.ndarray) and face_encoding.shape == (128,):
                        self.known_face_encodings.append(face_encoding)
                        self.known_face_names.append(student['name'])
                        self.known_face_ids.append(student['id'])
                        loaded_count += 1
                    else:
                        self.logger.warning(f"Invalid face encoding for student {student['name']}")
                        
                except Exception as e:
                    self.logger.error(f"Error loading face encoding for {student['name']}: {e}")
        
        self.logger.info(f"Loaded {loaded_count} valid face encodings")
        print(f"Loaded {loaded_count} known faces with enhanced validation")
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, List[str], List[Tuple]]:
        """Enhanced frame processing with multiple improvements"""
        self.frame_count += 1
        
        # Skip processing if not the right frame
        if not self.process_this_frame:
            self.process_this_frame = True
            # Return previous results scaled back up
            face_locations_scaled = [(top * 4, right * 4, bottom * 4, left * 4) 
                                   for (top, right, bottom, left) in self.face_locations]
            return frame, self.face_names, face_locations_scaled
        
        # Preprocess frame for better detection
        processed_frame = self.preprocess_frame(frame)
        
        # Resize frame for faster processing
        small_frame = cv2.resize(processed_frame, (0, 0), fx=0.25, fy=0.25)
        
        # Convert BGR to RGB
        rgb_small_frame = small_frame[:, :, ::-1]
        
        # Detect faces with multiple models
        self.face_locations, model_used = self.detect_faces_with_multiple_models(rgb_small_frame)
        
        # Get face encodings
        try:
            self.face_encodings = face_recognition.face_encodings(rgb_small_frame, self.face_locations)
        except Exception as e:
            self.logger.error(f"Error getting face encodings: {e}")
            self.face_encodings = []
        
        # Process each detected face
        self.face_names = []
        current_tolerance = self.adaptive_tolerance_adjustment(self.tolerance_history)
        
        for i, face_encoding in enumerate(self.face_encodings):
            # Get face location for quality assessment
            if i < len(self.face_locations):
                face_location = self.face_locations[i]
                
                # Extract face region for quality assessment
                top, right, bottom, left = face_location
                face_image = small_frame[top:bottom, left:right]
                
                # Assess face quality
                if face_image.size > 0:
                    quality_score = self.assess_face_quality(face_image, face_location)
                    
                    # Skip low-quality faces
                    if quality_score < self.face_quality_threshold:
                        self.face_names.append("Low Quality")
                        continue
                
                # Compare with known faces
                matches = face_recognition.compare_faces(
                    self.known_face_encodings, 
                    face_encoding, 
                    tolerance=current_tolerance
                )
                
                # Calculate face distances for confidence scoring
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                
                name = "Unknown"
                student_id = None
                confidence = 0.0
                
                if True in matches:
                    # Find best match
                    match_indices = [i for i, match in enumerate(matches) if match]
                    best_match_index = match_indices[0]
                    
                    if len(face_distances) > best_match_index:
                        # Calculate confidence (inverse of distance)
                        distance = face_distances[best_match_index]
                        confidence = max(0, 1 - distance)
                        
                        # Apply temporal smoothing
                        if len(match_indices) > 0:
                            potential_student_id = self.known_face_ids[best_match_index]
                            smoothed_confidence = self.smooth_detection_confidence(potential_student_id, confidence)
                            
                            # Accept match if smoothed confidence is high enough
                            if smoothed_confidence > 0.4:
                                name = self.known_face_names[best_match_index]
                                student_id = potential_student_id
                                
                                # Update statistics
                                self.detection_stats['successful_recognitions'] += 1
                
                # Update tolerance history
                self.tolerance_history.append(True if student_id else False)
                
                self.face_names.append(name)
                
                # Track student for attendance
                if student_id:
                    self.track_student_attendance(student_id, name, confidence)
                
                # Update detection statistics
                self.detection_stats['total_detections'] += 1
        
        # Switch processing flag
        self.process_this_frame = False
        
        # Scale back up face locations
        face_locations_scaled = [(top * 4, right * 4, bottom * 4, left * 4) 
                               for (top, right, bottom, left) in self.face_locations]
        
        return frame, self.face_names, face_locations_scaled
    
    def track_student_attendance(self, student_id: int, name: str, confidence: float = 1.0):
        """Enhanced student attendance tracking with confidence scoring"""
        current_time = time.time()
        
        if student_id not in self.student_tracking:
            self.student_tracking[student_id] = {
                'name': name,
                'first_seen': current_time,
                'last_seen': current_time,
                'entry_frames': 0,
                'exit_frames': 0,
                'status': 'unknown',
                'confidence_history': deque(maxlen=10),
                'avg_confidence': 0.0
            }
        
        # Update tracking data
        tracking = self.student_tracking[student_id]
        tracking['last_seen'] = current_time
        tracking['confidence_history'].append(confidence)
        tracking['avg_confidence'] = np.mean(list(tracking['confidence_history']))
        
        # Update frame counters based on current status
        if student_id in self.present_students:
            tracking['entry_frames'] += 1
            tracking['exit_frames'] = 0
        else:
            tracking['entry_frames'] += 1
            tracking['exit_frames'] = 0
    
    def get_attendance_updates(self) -> List[Dict]:
        """Get attendance updates with enhanced confidence filtering"""
        updates = []
        current_time = time.time()
        
        for student_id, tracking in self.student_tracking.items():
            # Check for entry with confidence threshold
            if (tracking['entry_frames'] >= self.entry_threshold and 
                student_id not in self.present_students and
                tracking['avg_confidence'] > 0.5):  # Confidence threshold
                
                self.present_students.add(student_id)
                tracking['status'] = 'entered'
                updates.append({
                    'student_id': student_id,
                    'name': tracking['name'],
                    'action': 'entered',
                    'time': current_time,
                    'confidence': tracking['avg_confidence']
                })
            
            # Check for exit (not seen for several frames)
            elif (current_time - tracking['last_seen'] > 5 and  # 5 seconds without detection
                  student_id in self.present_students):
                
                self.present_students.remove(student_id)
                tracking['status'] = 'exited'
                updates.append({
                    'student_id': student_id,
                    'name': tracking['name'],
                    'action': 'exited',
                    'time': current_time,
                    'confidence': tracking['avg_confidence']
                })
        
        return updates
    
    def get_current_present_students(self) -> List[int]:
        """Get list of currently present student IDs"""
        return list(self.present_students)
    
    def get_present_count(self) -> int:
        """Get current count of present students"""
        return len(self.present_students)
    
    def reset_tracking(self):
        """Reset tracking data"""
        self.present_students.clear()
        self.student_tracking.clear()
        self.detection_history.clear()
        self.tolerance_history.clear()
    
    def get_detection_stats(self) -> Dict:
        """Get detection performance statistics"""
        total = self.detection_stats['total_detections']
        if total > 0:
            success_rate = self.detection_stats['successful_recognitions'] / total
        else:
            success_rate = 0.0
        
        return {
            'total_detections': total,
            'successful_recognitions': self.detection_stats['successful_recognitions'],
            'success_rate': success_rate,
            'model_switches': self.detection_stats['model_switches'],
            'current_model': self.current_model,
            'current_tolerance': self.adaptive_tolerance_adjustment(list(self.tolerance_history))
        }
    
    def add_new_face(self, face_image: np.ndarray, name: str, student_id: int) -> bool:
        """Enhanced face addition with quality validation"""
        try:
            # Preprocess the image
            processed_image = self.preprocess_frame(face_image)
            
            # Convert BGR to RGB
            rgb_image = processed_image[:, :, ::-1]
            
            # Detect faces first
            face_locations = face_recognition.face_locations(rgb_image)
            
            if len(face_locations) == 0:
                self.logger.warning(f"No face detected in image for {name}")
                return False
            
            # Use the largest face if multiple detected
            if len(face_locations) > 1:
                face_areas = [(bottom - top) * (right - left) for top, right, bottom, left in face_locations]
                largest_face_idx = np.argmax(face_areas)
                face_location = face_locations[largest_face_idx]
            else:
                face_location = face_locations[0]
            
            # Assess face quality
            top, right, bottom, left = face_location
            face_region = rgb_image[top:bottom, left:right]
            quality_score = self.assess_face_quality(cv2.cvtColor(face_region, cv2.COLOR_RGB2BGR), face_location)
            
            if quality_score < self.face_quality_threshold:
                self.logger.warning(f"Face quality too low for {name}: {quality_score}")
                return False
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(rgb_image, [face_location])
            
            if len(face_encodings) > 0:
                face_encoding = face_encodings[0]
                
                # Validate encoding
                if face_encoding.shape == (128,):
                    self.known_face_encodings.append(face_encoding)
                    self.known_face_names.append(name)
                    self.known_face_ids.append(student_id)
                    
                    self.logger.info(f"Successfully added face for {name} with quality score: {quality_score}")
                    return True
                else:
                    self.logger.error(f"Invalid face encoding shape for {name}: {face_encoding.shape}")
                    return False
            else:
                self.logger.warning(f"Could not generate face encoding for {name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error adding new face for {name}: {e}")
            return False
    
    def detect_faces_in_image(self, image: np.ndarray) -> List[Tuple]:
        """Enhanced face detection in image"""
        processed_image = self.preprocess_frame(image)
        rgb_image = processed_image[:, :, ::-1]
        
        face_locations, _ = self.detect_faces_with_multiple_models(rgb_image)
        return face_locations
    
    def get_face_encoding(self, image: np.ndarray, face_location: Tuple) -> Optional[np.ndarray]:
        """Get face encoding with preprocessing"""
        try:
            processed_image = self.preprocess_frame(image)
            rgb_image = processed_image[:, :, ::-1]
            
            face_encodings = face_recognition.face_encodings(rgb_image, [face_location])
            
            if len(face_encodings) > 0:
                return face_encodings[0]
            else:
                return None
        except Exception as e:
            self.logger.error(f"Error getting face encoding: {e}")
            return None
    
    def add_multiple_face_angles(self, face_images: List[np.ndarray], name: str, student_id: int) -> bool:
        """Add multiple face angles for better recognition"""
        try:
            successful_encodings = 0
            
            for i, face_image in enumerate(face_images):
                # Detect and add face
                if self.add_new_face(face_image, name, student_id):
                    successful_encodings += 1
            
            if successful_encodings > 0:
                self.logger.info(f"Successfully added {successful_encodings} face encodings for {name}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error adding multiple face angles: {e}")
            return False

    def _create_face_variations(self, face_encoding: np.ndarray) -> List[np.ndarray]:
        """Create variations of a face encoding for better recognition (placeholder for compatibility)"""
        # For the enhanced module using face_recognition lib, variations aren't as simple as image transforms
        # But we return a list with the original for compatibility
        return [face_encoding]

    def optimize_performance(self):
        """Optimize performance based on detection statistics"""
        stats = self.get_detection_stats()
        
        # Switch to faster model if success rate is high
        if stats['success_rate'] > 0.8 and self.current_model == 'cnn':
            self.current_model = 'hog'
            self.logger.info("Switched to HOG model for better performance")
        
        # Switch to more accurate model if success rate is low
        elif stats['success_rate'] < 0.4 and self.current_model == 'hog':
            self.current_model = 'cnn'
            self.logger.info("Switched to CNN model for better accuracy")
        
        # Adjust detection interval based on performance
        if stats['total_detections'] > 100:
            if stats['success_rate'] > 0.9:
                self.detection_interval = 3  # Process fewer frames
            elif stats['success_rate'] < 0.3:
                self.detection_interval = 1  # Process more frames

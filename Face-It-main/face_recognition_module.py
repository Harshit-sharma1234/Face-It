"""
Compatibility wrapper for enhanced face recognition module
This ensures backward compatibility with existing code
"""

from enhanced_face_recognition_module import EnhancedFaceRecognitionModule

# Create an alias for backward compatibility
FaceRecognitionModule = EnhancedFaceRecognitionModule

# Export the class for direct import
__all__ = ['FaceRecognitionModule', 'EnhancedFaceRecognitionModule']

#!/usr/bin/env python3
"""
GitHub Setup Script for Face-It Project
Automatically initializes Git repository and pushes to GitHub
"""

import os
import subprocess
import sys

def run_command(command, cwd=None):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, 
                              capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def setup_git_repository():
    """Initialize Git repository and set up for GitHub"""
    
    print("🚀 Setting up Face-It project for GitHub...")
    
    # Get current directory
    project_dir = os.getcwd()
    print(f"Working in: {project_dir}")
    
    # Initialize Git repository
    print("\n1. Initializing Git repository...")
    success, output = run_command("git init", project_dir)
    if success:
        print("✓ Git repository initialized")
    else:
        print(f"✗ Failed to initialize Git: {output}")
        return False
    
    # Create .gitignore file
    print("\n2. Creating .gitignore file...")
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Database
*.db
*.sqlite3

# Logs
*.log

# Face recognition data
face_data/
student_photos/
temp_photos/

# Backup files
*_backup_*
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)
    print("✓ .gitignore created")
    
    # Add all files
    print("\n3. Adding files to Git...")
    success, output = run_command("git add .", project_dir)
    if success:
        print("✓ Files added to Git")
    else:
        print(f"✗ Failed to add files: {output}")
        return False
    
    # Initial commit
    print("\n4. Creating initial commit...")
    commit_message = "Enhanced Face-It attendance system with improved face detection"
    success, output = run_command(f'git commit -m "{commit_message}"', project_dir)
    if success:
        print("✓ Initial commit created")
    else:
        print(f"✗ Failed to create commit: {output}")
        return False
    
    # Add remote origin
    print("\n5. Adding GitHub remote...")
    github_url = "https://github.com/Harshit-sharma1234/Face-It.git"
    success, output = run_command(f"git remote add origin {github_url}", project_dir)
    if success:
        print("✓ GitHub remote added")
    else:
        # Remote might already exist, try to set URL
        success, output = run_command(f"git remote set-url origin {github_url}", project_dir)
        if success:
            print("✓ GitHub remote URL updated")
        else:
            print(f"⚠ Remote setup issue: {output}")
    
    # Set main branch
    print("\n6. Setting up main branch...")
    success, output = run_command("git branch -M main", project_dir)
    if success:
        print("✓ Main branch set")
    else:
        print(f"⚠ Branch setup: {output}")
    
    # Push to GitHub
    print("\n7. Pushing to GitHub...")
    print("Note: You may need to authenticate with GitHub")
    success, output = run_command("git push -u origin main", project_dir)
    if success:
        print("✅ Successfully pushed to GitHub!")
        print(f"🌐 Your repository is available at: {github_url}")
    else:
        print(f"❌ Failed to push to GitHub: {output}")
        print("\n📝 Manual steps needed:")
        print("1. Make sure you're logged into GitHub")
        print("2. Run: git push -u origin main")
        print("3. Or use GitHub Desktop/VS Code Git integration")
        return False
    
    return True

def create_readme():
    """Create an enhanced README for the project"""
    readme_content = """# Face-It - Enhanced Attendance System

An intelligent face recognition-based attendance tracking system with advanced computer vision capabilities.

## 🚀 Enhanced Features

### Core Functionality
- **Real-time Face Detection & Recognition**: Advanced face detection using multiple models
- **Automated Attendance Tracking**: Seamless entry/exit tracking
- **Student Management**: Easy student registration and management
- **Database Integration**: SQLite database for reliable data storage

### Enhanced Capabilities (New!)
- **Adaptive Lighting Compensation**: Works in various lighting conditions
- **Multiple Detection Models**: HOG + CNN models for robustness
- **Dynamic Tolerance Adjustment**: Self-optimizing recognition accuracy
- **Face Quality Assessment**: Filters out low-quality detections
- **Temporal Smoothing**: Stable tracking with reduced false positives
- **Performance Monitoring**: Real-time statistics and optimization

## 🛠️ Technical Improvements

### Image Preprocessing
- CLAHE (Contrast Limited Adaptive Histogram Equalization)
- Bilateral filtering for noise reduction
- Automatic brightness and contrast adjustment
- LAB color space processing for better lighting handling

### Detection Algorithms
- Dual-model approach (HOG for speed, CNN for accuracy)
- Automatic model switching based on performance
- Face quality scoring and filtering
- Confidence-based recognition with temporal smoothing

### Tracking Enhancements
- Improved entry/exit detection algorithms
- Confidence-weighted attendance decisions
- Reduced false positive rates
- Better handling of partial occlusions

## 📋 Requirements

```
opencv-python>=4.5.0
face-recognition>=1.3.0
numpy>=1.21.0
Pillow>=8.0.0
tkinter (usually comes with Python)
```

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/Harshit-sharma1234/Face-It.git
cd Face-It
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main_gui.py
```

## 💡 Usage

### First Time Setup
1. Launch the application
2. Add students using the "Student Management" section
3. Capture face photos for each student
4. Start attendance tracking

### Daily Operation
1. Start the camera feed
2. Begin attendance tracking
3. Students will be automatically detected and tracked
4. View real-time attendance status
5. Export attendance reports as needed

## 🔧 Configuration

The enhanced system automatically adapts to different environments, but you can customize:

- Detection sensitivity in `enhanced_face_recognition_module.py`
- Camera settings in `camera_module.py`
- Database configuration in `database.py`

## 📊 Performance Features

- **Real-time Statistics**: Monitor detection success rates
- **Automatic Optimization**: System self-tunes for best performance
- **Quality Metrics**: Face quality assessment and filtering
- **Environmental Adaptation**: Automatic adjustment to lighting conditions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- OpenCV community for computer vision tools
- face_recognition library by Adam Geitgey
- Python community for excellent libraries

## 📞 Support

For issues and questions, please open an issue on GitHub or contact the maintainer.

---

**Enhanced by AI Assistant with advanced computer vision capabilities**
"""
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("✓ Enhanced README.md created")

def create_requirements():
    """Create requirements.txt file"""
    requirements = """opencv-python>=4.5.0
face-recognition>=1.3.0
numpy>=1.21.0
Pillow>=8.0.0
"""
    
    with open("requirements.txt", "w") as f:
        f.write(requirements)
    print("✓ requirements.txt created")

def main():
    """Main setup function"""
    print("🎯 Face-It GitHub Setup")
    print("=" * 40)
    
    # Create project files
    create_readme()
    create_requirements()
    
    # Setup Git and push to GitHub
    if setup_git_repository():
        print("\n🎉 Setup completed successfully!")
        print("\n📋 What's been done:")
        print("• Enhanced face recognition module added")
        print("• Git repository initialized")
        print("• Files committed to Git")
        print("• Pushed to GitHub repository")
        print("• README and requirements.txt created")
        
        print("\n🔗 Next steps:")
        print("• Visit your GitHub repository to verify")
        print("• Share the repository link with others")
        print("• Consider adding more documentation")
        
    else:
        print("\n⚠️ Setup completed with some manual steps needed")
        print("Please check the messages above for next steps")

if __name__ == "__main__":
    main()

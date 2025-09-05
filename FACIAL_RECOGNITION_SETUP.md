# Facial Recognition Setup Guide

## 🎯 **Facial Verification System Implementation**

This guide explains how to set up the facial recognition system for tournament photo verification.

## 📋 **Prerequisites**

### **Option 1: Simple Installation (Recommended for Testing)**
```bash
# Install basic dependencies
pip install opencv-python==4.8.1.78
pip install Pillow==10.0.1
pip install numpy==1.24.3

# Install face_recognition (this may take a while)
pip install face_recognition==1.3.0
```

### **Option 2: Full Installation (For Production)**
```bash
# Install all dependencies from requirements file
pip install -r requirements_facial_recognition.txt
```

## 🔧 **Installation Steps**

### **Step 1: Install Dependencies**
```bash
# Navigate to your project directory
cd C:\Users\User\Documents\safa_connect

# Activate virtual environment
venv\Scripts\activate

# Install facial recognition packages
pip install opencv-python Pillow numpy face_recognition
```

### **Step 2: Test Installation**
```bash
# Test if face_recognition is working
python -c "import face_recognition; print('Face recognition installed successfully!')"
```

### **Step 3: Restart Django Server**
```bash
# Restart your Django development server
python manage.py runserver
```

## 🚀 **How to Use Facial Verification**

### **1. Automatic Verification**
- Go to: `http://localhost:8000/tournaments/admin/verify/`
- Click **"Auto-Verify"** button on any registration
- System will automatically compare live photo against stored photos
- Results show confidence percentage and verification status

### **2. Upload Reference Photo**
- Click **"Upload Reference"** button
- Select a clear photo of the person's face
- System will immediately verify against the uploaded reference
- Shows detailed results with confidence score

### **3. Verification Results**
- **✅ VERIFIED**: High confidence (>70%) - Person is verified
- **⚠️ MANUAL_REVIEW**: Medium confidence (50-70%) - Needs human review
- **❌ FAILED**: Low confidence (<50%) - Verification failed

## 🎯 **How It Works**

### **Facial Recognition Process:**
1. **Face Detection**: Finds faces in both live and reference photos
2. **Feature Extraction**: Extracts 128 facial feature points
3. **Comparison**: Compares feature vectors using Euclidean distance
4. **Confidence Score**: Calculates similarity percentage (0-100%)
5. **Decision**: Automatically determines verification status

### **Technical Details:**
- Uses **dlib** library for face detection and encoding
- **HOG (Histogram of Oriented Gradients)** for face detection
- **128-dimensional face encodings** for comparison
- **Tolerance threshold**: 0.6 (adjustable for stricter/looser matching)

## 🔧 **Configuration Options**

### **Adjust Verification Sensitivity:**
Edit `tournament_verification/facial_verification.py`:

```python
class FacialVerification:
    def __init__(self):
        self.tolerance = 0.6  # Lower = more strict (0.4-0.8 range)
        self.face_detection_model = 'hog'  # 'hog' or 'cnn'
```

### **Confidence Thresholds:**
Edit `tournament_verification/views.py` in `auto_verify_registration`:

```python
# Adjust these thresholds
if verification_result['verified'] and verification_result['confidence'] > 0.7:  # 70%
    status = 'VERIFIED'
elif verification_result['confidence'] > 0.5:  # 50%
    status = 'MANUAL_REVIEW'
```

## 🐛 **Troubleshooting**

### **Common Issues:**

#### **1. "No module named 'face_recognition'"**
```bash
pip install face_recognition
```

#### **2. "No module named 'cv2'"**
```bash
pip install opencv-python
```

#### **3. "dlib installation failed"**
```bash
# Try alternative installation
pip install dlib-binary
# Or install Visual Studio Build Tools first
```

#### **4. "No face detected"**
- Ensure photos have clear, well-lit faces
- Face should be looking directly at camera
- Avoid sunglasses, hats, or face coverings
- Minimum face size: 100x100 pixels

### **Performance Tips:**
- Use **'hog'** model for faster processing
- Use **'cnn'** model for better accuracy (slower)
- Resize large images before processing
- Process images in batches for better performance

## 📊 **Expected Results**

### **Good Quality Photos:**
- **Confidence**: 80-95%
- **Verification**: Usually successful
- **Processing Time**: 1-3 seconds

### **Poor Quality Photos:**
- **Confidence**: 30-60%
- **Verification**: May require manual review
- **Issues**: Blurry, dark, side angle, multiple faces

## 🔒 **Security Considerations**

- Photos are stored securely in Django media files
- Face encodings are not stored (only calculated during verification)
- All verification attempts are logged
- Access restricted to superusers only

## 🎉 **Ready to Use!**

Once installed, the facial verification system will be available in your tournament admin dashboard. Players can register with live photos, and administrators can verify them automatically using AI-powered facial recognition!

## 📞 **Support**

If you encounter issues:
1. Check the Django logs for error messages
2. Verify all dependencies are installed correctly
3. Test with high-quality, well-lit photos first
4. Adjust tolerance settings if needed




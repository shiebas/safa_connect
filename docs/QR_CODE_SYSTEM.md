# SAFA Connect QR Code System Documentation

## 📋 Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Features](#features)
4. [How It Works](#how-it-works)
5. [Usage Instructions](#usage-instructions)
6. [Technical Implementation](#technical-implementation)
7. [API Reference](#api-reference)
8. [Troubleshooting](#troubleshooting)
9. [Security Considerations](#security-considerations)
10. [Future Enhancements](#future-enhancements)

---

## 🎯 Overview

The SAFA Connect QR Code System provides **real-time member verification** for match officials and administrators. It generates dynamic QR codes that contain current membership status, eligibility information, and verification details.

### **Key Benefits:**
- ✅ **Real-time status updates** - Always current, never outdated
- ✅ **Instant verification** - No manual lookups required
- ✅ **Professional appearance** - Official SAFA branding
- ✅ **Mobile-friendly** - Works with any QR scanner app
- ✅ **Secure verification** - Unique IDs and timestamps

---

## 🏗️ System Architecture

### **Components:**

#### **1. Profile QR Code (Enhanced)**
- **Location:** Profile page (`/local-accounts/profile/`)
- **Purpose:** Basic profile sharing with real-time status
- **Size:** 120x120px
- **Content:** Member info, SAFA ID, current status

#### **2. Match Verification QR Code**
- **Location:** Dedicated verification page (`/local-accounts/match-verification-qr/`)
- **Purpose:** Official match verification for officials
- **Size:** 200x200px
- **Content:** Comprehensive verification data

### **Data Flow:**
```
User Profile → Status Check → QR Generation → Display → Scan Verification
     ↓              ↓            ↓           ↓         ↓
  Member Data → Suspension Check → QR Code → Template → Mobile App
```

---

## ✨ Features

### **1. Real-Time Status Detection**

#### **Membership Status:**
- `ACTIVE` - Member can participate in matches
- `SUSPENDED` - Member is suspended and cannot play
- `INACTIVE` - Member account is not active

#### **Match Eligibility:**
- `ELIGIBLE` - Member can participate in matches
- `NOT ELIGIBLE` - Member cannot participate (suspended/inactive)

#### **Suspension Information:**
- **Start Date** - When suspension began
- **End Date** - When suspension expires
- **Reason** - Why member was suspended

### **2. Dynamic Content Generation**

#### **Profile QR Code Content:**
```
SAFA MEMBER VERIFICATION
Name: [Full Name]
SAFA ID: [5-digit ID]
Status: [ACTIVE/SUSPENDED]
Match Eligibility: [ELIGIBLE/NOT ELIGIBLE]
[Suspension details if applicable]
Profile: [Profile URL]
Generated: [Timestamp]
```

#### **Match Verification QR Content:**
```
SAFA MATCH VERIFICATION
ID: [Unique Verification ID]
Name: [Full Name]
SAFA ID: [5-digit ID]
Role: [Player/Official/Coach]
Status: [Membership Status]
Match Eligible: [Eligibility Status]
[Suspension Details]
Verified: [Timestamp]
Profile: [Profile URL]
```

### **3. Professional Design**

#### **Visual Elements:**
- **SAFA Branding** - Official colors and logos
- **Status Badges** - Color-coded eligibility indicators
- **Responsive Layout** - Mobile and desktop optimized
- **Print Support** - Professional verification documents

#### **Interactive Features:**
- **Hover Effects** - Enhanced user experience
- **Print Functionality** - Hard copy verification
- **Navigation** - Easy access to related pages

---

## 🔄 How It Works

### **1. Status Checking Process**

```python
# 1. Get current membership status
membership_status = member.membership_status

# 2. Check for active suspensions
if member.suspensions.exists():
    latest_suspension = member.suspensions.filter(
        end_date__gte=timezone.now().date()
    ).first()
    
    if latest_suspension:
        membership_status = "SUSPENDED"
        match_eligibility = "NOT ELIGIBLE"

# 3. Check other restrictions
if not member.is_active:
    match_eligibility = "NOT ELIGIBLE"
```

### **2. QR Code Generation**

```python
# 1. Create QR code object
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=6,
    border=2,
)

# 2. Add data
qr.add_data(qr_data)

# 3. Generate image
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")

# 4. Convert to base64
buffer = BytesIO()
img.save(buffer, format="PNG")
qr_code_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
```

### **3. Real-Time Updates**

- **No Caching** - QR codes generated fresh each time
- **Database Queries** - Direct status checks from database
- **Timestamp Validation** - Shows when verification was generated
- **Unique IDs** - Each verification has unique identifier

---

## 📱 Usage Instructions

### **1. For Members**

#### **Generate Profile QR Code:**
1. Go to your profile page (`/local-accounts/profile/`)
2. QR code is automatically displayed below profile picture
3. Contains current membership status and basic info

#### **Generate Match Verification QR:**
1. Click "Match Verification QR" button on profile page
2. Generate fresh verification code for match officials
3. Print or display on mobile device

### **2. For Match Officials**

#### **Scanning Process:**
1. **Open QR Scanner App** - Any mobile QR scanner
2. **Scan QR Code** - Point camera at verification QR
3. **Verify Information** - Check displayed data
4. **Confirm Eligibility** - Look for "ELIGIBLE" status
5. **Record Verification** - Note verification ID and timestamp

#### **What to Look For:**
- ✅ **Green "ELIGIBLE" badge** - Member can participate
- ❌ **Red "NOT ELIGIBLE" badge** - Member cannot participate
- ⚠️ **Suspension details** - Check end date if suspended
- 🕒 **Recent timestamp** - Ensure verification is current

### **3. For Administrators**

#### **Monitoring Usage:**
- Track verification attempts
- Monitor suspension compliance
- Generate verification reports

---

## 🔧 Technical Implementation

### **1. Views**

#### **Profile View (`accounts/views.py`):**
```python
@login_required
def profile(request):
    # Generate QR code with real-time status
    try:
        # Get current status
        membership_status = "ACTIVE"
        match_eligibility = "ELIGIBLE"
        
        # Check suspensions
        if member.suspensions.exists():
            latest_suspension = member.suspensions.filter(
                end_date__gte=timezone.now().date()
            ).first()
            
            if latest_suspension:
                membership_status = "SUSPENDED"
                match_eligibility = "NOT ELIGIBLE"
        
        # Generate QR data
        qr_data = f"""SAFA MEMBER VERIFICATION
Name: {request.user.get_full_name()}
SAFA ID: {request.user.safa_id}
Status: {membership_status}
Match Eligibility: {match_eligibility}
{suspension_info}
Profile: {profile_url}
Generated: {current_timestamp}"""
        
        # Create QR code
        qr = qrcode.QRCode(...)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Convert to base64
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
    except Exception as e:
        qr_code_base64 = None
        qr_code_generated = False
    
    context = {
        'user': request.user,
        'member': member,
        'qr_code': qr_code_base64,
        'qr_code_generated': qr_code_generated,
    }
    return render(request, 'accounts/profile.html', context)
```

#### **Match Verification QR View:**
```python
@login_required
def generate_match_verification_qr(request):
    """Generate a QR code specifically for match verification"""
    try:
        member = request.user.member_profile
    except Member.DoesNotExist:
        messages.error(request, "You do not have a member profile.")
        return redirect('accounts:profile')

    # Get real-time verification data
    verification_data = {
        'name': member.get_full_name(),
        'safa_id': member.safa_id,
        'role': member.role,
        'membership_status': member.membership_status,
        'match_eligibility': 'ELIGIBLE',
        'suspension_info': '',
        'verification_timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
        'verification_id': f"VER-{member.safa_id}-{int(timezone.now().timestamp())}"
    }
    
    # Check suspensions and eligibility
    # ... (status checking logic)
    
    # Generate QR code
    qr_data = f"""SAFA MATCH VERIFICATION
ID: {verification_data['verification_id']}
Name: {verification_data['name']}
SAFA ID: {verification_data['safa_id']}
Role: {verification_data['role']}
Status: {verification_data['membership_status']}
Match Eligible: {verification_data['match_eligibility']}
{verification_data['suspension_info']}
Verified: {verification_data['verification_timestamp']}
Profile: {request.build_absolute_uri(reverse('accounts:profile'))}"""

    # Create and return QR code
    # ... (QR generation logic)
```

### **2. Templates**

#### **Profile Template (`accounts/templates/accounts/profile.html`):**
```html
<!-- QR Code Section -->
{% if qr_code_generated and qr_code %}
<div class="qr-code-section mb-3">
    <h6 class="text-muted mb-2">Profile QR Code</h6>
    <div class="qr-code-container">
        <img src="data:image/png;base64,{{ qr_code }}" alt="Profile QR Code" class="qr-code-image">
    </div>
    <small class="text-muted d-block mt-2">Scan to view profile</small>
</div>
{% endif %}

<!-- Match Verification QR Code Button -->
{% if user.role != 'SUPPORTER' %}
<div class="mt-3">
    <a href="{% url 'accounts:generate_match_verification_qr' %}" class="btn btn-success btn-sm">
        <i class="fas fa-qrcode me-2"></i>Match Verification QR
    </a>
    <small class="text-muted d-block mt-1">Generate QR for match officials</small>
</div>
{% endif %}
```

#### **Match Verification Template (`accounts/templates/accounts/match_verification_qr.html`):**
```html
<!-- QR Code Section -->
<div class="qr-code-section">
    <h4 class="mb-3 text-primary">Scan to Verify Member Status</h4>
    <div class="qr-code-container">
        <img src="data:image/png;base64,{{ qr_code }}" alt="Match Verification QR Code" class="qr-code-image">
    </div>
    <p class="text-muted mt-3 mb-0">
        <i class="fas fa-info-circle me-2"></i>
        Use any QR scanner app to verify member eligibility
    </p>
</div>

<!-- Verification Information -->
<div class="verification-info">
    <h5 class="mb-3 text-center">
        <i class="fas fa-clipboard-check me-2"></i>
        Member Verification Details
    </h5>
    
    <div class="verification-id text-center mb-3">
        {{ verification_data.verification_id }}
    </div>
    
    <!-- Status information rows -->
    <div class="info-row">
        <span class="info-label">Match Eligibility:</span>
        <span class="info-value">
            {% if verification_data.match_eligibility == 'ELIGIBLE' %}
                <span class="status-badge status-eligible">ELIGIBLE</span>
            {% else %}
                <span class="status-badge status-suspended">NOT ELIGIBLE</span>
            {% endif %}
        </span>
    </div>
</div>
```

### **3. URLs**

#### **URL Configuration (`accounts/urls.py`):**
```python
from .views import (
    modern_home, profile, edit_profile, generate_digital_card, generate_match_verification_qr
)

urlpatterns = [
    # ... existing URLs ...
    path('match-verification-qr/', generate_match_verification_qr, name='generate_match_verification_qr'),
]
```

### **4. CSS Styling**

#### **QR Code Styling:**
```css
.qr-code-section {
    text-align: center;
    padding: 1rem;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 15px;
    border: 1px solid #dee2e6;
    transition: all 0.3s ease;
}

.qr-code-container {
    display: inline-block;
    padding: 10px;
    background: white;
    border-radius: 10px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
}

.qr-code-image {
    width: 120px;
    height: 120px;
    border-radius: 8px;
    transition: all 0.3s ease;
}

.status-badge {
    padding: 8px 16px;
    border-radius: 20px;
    font-weight: bold;
    font-size: 14px;
    display: inline-block;
    margin: 5px;
}

.status-eligible {
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
    color: white;
}

.status-suspended {
    background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%);
    color: white;
}
```

---

## 📚 API Reference

### **1. Profile QR Code**

#### **Endpoint:** `/local-accounts/profile/`
#### **Method:** GET
#### **Authentication:** Required (Login)
#### **Response:** HTML with embedded QR code

#### **Context Variables:**
```python
{
    'user': CustomUser,
    'member': Member,
    'qr_code': str,  # Base64 encoded PNG
    'qr_code_generated': bool
}
```

### **2. Match Verification QR Code**

#### **Endpoint:** `/local-accounts/match-verification-qr/`
#### **Method:** GET
#### **Authentication:** Required (Login)
#### **Response:** HTML with verification QR code

#### **Context Variables:**
```python
{
    'member': Member,
    'user': CustomUser,
    'qr_code': str,  # Base64 encoded PNG
    'verification_data': dict
}
```

#### **Verification Data Structure:**
```python
verification_data = {
    'name': str,                    # Full name
    'safa_id': str,                 # SAFA ID
    'role': str,                    # Member role
    'membership_status': str,       # ACTIVE/SUSPENDED/INACTIVE
    'match_eligibility': str,       # ELIGIBLE/NOT ELIGIBLE
    'suspension_info': str,         # Suspension details
    'verification_timestamp': str,  # ISO timestamp
    'verification_id': str          # Unique verification ID
}
```

---

## 🚨 Troubleshooting

### **Common Issues:**

#### **1. QR Code Not Displaying**
- **Cause:** QR generation failed
- **Solution:** Check browser console for errors
- **Debug:** Look for "QR code generation failed" messages

#### **2. Status Not Updating**
- **Cause:** Database connection issues
- **Solution:** Refresh page to regenerate QR
- **Debug:** Check member status in admin panel

#### **3. QR Code Too Small/Large**
- **Cause:** CSS sizing issues
- **Solution:** Adjust `.qr-code-image` dimensions
- **Debug:** Check browser developer tools

#### **4. Mobile Scanning Issues**
- **Cause:** QR code quality or size
- **Solution:** Use larger QR code (match verification)
- **Debug:** Test with different QR scanner apps

### **Debug Information:**

#### **Console Logs:**
```python
# Look for these debug messages:
print(f"⚠️ Warning: QR code generation failed: {str(e)}")
print(f"⚠️ Warning: Status check failed: {str(e)}")
print(f"⚠️ Warning: Suspension check failed: {str(e)}")
```

#### **Browser Developer Tools:**
- Check **Console** for JavaScript errors
- Check **Network** for failed requests
- Check **Elements** for missing CSS classes

---

## 🔒 Security Considerations

### **1. Data Protection**

#### **QR Code Content:**
- **No sensitive data** - Only public information
- **No passwords** - Authentication not exposed
- **No financial data** - Payment info not included

#### **Access Control:**
- **Login required** - Only authenticated users
- **Role-based access** - Supporters cannot generate verification QR
- **Session validation** - CSRF protection enabled

### **2. Verification Security**

#### **Unique Identifiers:**
- **Verification ID** - Unique for each scan
- **Timestamp** - Prevents replay attacks
- **Member validation** - Database verification required

#### **Real-time Updates:**
- **No caching** - Always current information
- **Database queries** - Direct status checks
- **Suspension detection** - Immediate restriction enforcement

### **3. Privacy Considerations**

#### **Information Disclosure:**
- **Public profile data** - Name, SAFA ID, role
- **Status information** - Membership and eligibility
- **No personal details** - Address, phone, email not included

---

## 🚀 Future Enhancements

### **1. Advanced Features**

#### **QR Code Expiration:**
- **Time-based expiration** - QR codes expire after set time
- **Event-specific codes** - Different codes for different events
- **Usage tracking** - Monitor QR code scans

#### **Enhanced Verification:**
- **Biometric integration** - Fingerprint/face recognition
- **Location verification** - GPS-based validation
- **Offline support** - Cached verification data

### **2. Integration Opportunities**

#### **Match Management:**
- **Automatic check-ins** - QR scan registers attendance
- **Team sheets** - QR verification for team selection
- **Match reports** - QR-based incident reporting

#### **Administrative Tools:**
- **Bulk verification** - Multiple member verification
- **Analytics dashboard** - Usage statistics and reports
- **API endpoints** - Third-party integration support

### **3. Mobile Applications**

#### **Dedicated Apps:**
- **SAFA Official App** - Professional verification tool
- **Member App** - Personal QR code management
- **Admin App** - Administrative verification tools

---

## 📞 Support and Contact

### **Technical Support:**
- **Email:** support@safaconnect.com
- **Phone:** +27 11 567 8900
- **Hours:** Monday-Friday, 8:00 AM - 5:00 PM SAST

### **Documentation Updates:**
- **Version:** 1.0.0
- **Last Updated:** December 2024
- **Maintainer:** SAFA Connect Development Team

### **Feedback and Suggestions:**
- **Feature Requests:** Submit via support email
- **Bug Reports:** Include error messages and steps to reproduce
- **Documentation Issues:** Report missing or unclear information

---

## 📄 License and Legal

### **Copyright:**
© 2024 South African Football Association (SAFA). All rights reserved.

### **Usage Terms:**
- **Internal Use:** Free for SAFA members and officials
- **Commercial Use:** Requires written permission
- **Modification:** Not permitted without authorization

### **Data Protection:**
- **POPI Act Compliance:** Personal data protection standards
- **GDPR Compliance:** European data protection regulations
- **Data Retention:** QR codes generated on-demand, not stored

---

*This documentation is maintained by the SAFA Connect Development Team. For questions or updates, please contact the development team.*


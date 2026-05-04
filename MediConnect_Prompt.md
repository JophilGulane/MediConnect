# MediConnect — Full Step-by-Step Development Prompt
### Stack: Django · SQLite · Tailwind CSS · PythonAnywhere

---

## Project Overview

**App Name:** MediConnect  
**Type:** E-Consultation / Telemedicine Web Application  
**Purpose:** Connect patients to licensed doctors for real-time online consultations, image-based diagnosis, live chat, and printable digital prescriptions.  
**Deployment Target:** PythonAnywhere (Free or Paid tier)

---

## PHASE 1 — Requirements & Architecture Planning

### Step 1: Define Functional Requirements

**Patient Side**
- Register and log in with email and password
- Create and edit a personal health profile (age, gender, blood type, medical history)
- Browse available/online doctors filtered by specialty
- Submit a consultation request with a symptom description
- Upload images during consultation (skin conditions, wounds, visible symptoms)
- Real-time chat with an assigned doctor using Django Channels
- Receive a downloadable, printable prescription at the end of the consultation
- View full consultation history

**Doctor Side**
- Register with professional credentials (license number, specialty)
- Secure login panel with a personal dashboard
- Toggle availability status (Online / Offline / Busy)
- View incoming patient consultation requests in a live queue
- Accept the next patient from the queue
- Chat with the patient in real time
- View all images uploaded by the patient
- Generate and send a digital prescription as a downloadable file
- View past consultation records and prescriptions issued

**Admin Side**
- Approve or reject doctor registrations
- Monitor all active and completed consultations
- Manage patients and doctors (view, suspend, delete)
- View system statistics (total users, consultations per day, etc.)

---

### Step 2: Define Non-Functional Requirements

- Real-time chat with sub-second latency using Django Channels + WebSockets
- Image uploads limited to JPEG, PNG, WEBP — max 5MB each
- Prescriptions downloadable as PDF (generated server-side with ReportLab)
- Mobile-responsive UI using Tailwind CSS
- Role-based access control: Patient, Doctor, Admin
- All sensitive data encrypted in transit (HTTPS on PythonAnywhere)
- SQLite as the database (single-file, zero-config, ideal for PythonAnywhere)

---

### Step 3: Final Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | Django 4.x |
| Real-Time | Django Channels + Daphne (ASGI) |
| Database | SQLite (via Django ORM) |
| Frontend Styling | Tailwind CSS (CDN) |
| Templating | Django Templates (Jinja2-compatible) |
| Authentication | Django built-in auth + django-allauth |
| File Storage | Django default local media storage |
| PDF Generation | ReportLab |
| Forms | Django Forms + django-crispy-forms |
| Notifications | Django messages framework + WebSocket events |
| Deployment | PythonAnywhere (WSGI + ASGI) |

> **Note on Django Channels on PythonAnywhere:** PythonAnywhere's free tier does not support WebSockets. If using the free tier, replace real-time chat with an AJAX long-polling fallback (polling every 2 seconds). On a paid PythonAnywhere plan, Django Channels with Daphne runs fully.

---

### Step 4: Design the Database Models

Plan the following Django models before writing any code:

**User** (extends AbstractUser)
```
role: CharField [patient | doctor | admin]
phone: CharField
profile_picture: ImageField
```

**PatientProfile**
```
user: OneToOneField(User)
date_of_birth: DateField
gender: CharField
blood_type: CharField
allergies: TextField
medical_history: TextField
emergency_contact: CharField
```

**DoctorProfile**
```
user: OneToOneField(User)
specialty: CharField
license_number: CharField
bio: TextField
years_of_experience: IntegerField
availability_status: CharField [online | offline | busy]
is_verified: BooleanField (default False)
rating: DecimalField
```

**Consultation**
```
patient: ForeignKey(User)
doctor: ForeignKey(User)
status: CharField [pending | active | completed | cancelled]
symptoms_description: TextField
created_at: DateTimeField
started_at: DateTimeField (nullable)
ended_at: DateTimeField (nullable)
```

**Message**
```
consultation: ForeignKey(Consultation)
sender: ForeignKey(User)
message_type: CharField [text | image]
content: TextField (text message or image URL)
sent_at: DateTimeField
```

**ConsultationImage**
```
consultation: ForeignKey(Consultation)
uploaded_by: ForeignKey(User)
image: ImageField
uploaded_at: DateTimeField
```

**Prescription**
```
consultation: OneToOneField(Consultation)
doctor: ForeignKey(User)
patient: ForeignKey(User)
medicines: JSONField (list of {name, dosage, frequency, duration})
notes: TextField
instructions: TextField
issued_at: DateTimeField
pdf_file: FileField (nullable)
```

---

## PHASE 2 — Project Setup

### Step 5: Create the Django Project

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install django django-allauth django-crispy-forms channels daphne
pip install pillow reportlab django-widget-tweaks

# Start the project and app
django-admin startproject mediconnect .
python manage.py startapp accounts
python manage.py startapp consultations
python manage.py startapp prescriptions
python manage.py startapp dashboard
```

### Step 6: Configure settings.py

```python
INSTALLED_APPS = [
    'daphne',              # Must be first for ASGI
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'crispy_forms',
    'widget_tweaks',
    'allauth',
    'allauth.account',
    'accounts',
    'consultations',
    'prescriptions',
    'dashboard',
]

AUTH_USER_MODEL = 'accounts.User'

# Database — SQLite (default, no changes needed)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ASGI + Channels
ASGI_APPLICATION = 'mediconnect.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
        # For production: use channels_redis.core.RedisChannelLayer
    }
}

# File uploads
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Auth
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Crispy forms
CRISPY_TEMPLATE_PACK = 'tailwind'
```

### Step 7: Configure asgi.py for Django Channels

```python
# mediconnect/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import consultations.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediconnect.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(consultations.routing.websocket_urlpatterns)
    ),
})
```

### Step 8: Set Up Tailwind CSS

In `base.html`, link the Tailwind CDN:

```html
<script src="https://cdn.tailwindcss.com"></script>
```

For a production build (optional), install Tailwind via npm and compile to a static CSS file, then reference that in your templates instead of the CDN.

Create a `templates/` folder at the project root and add to `settings.py`:

```python
TEMPLATES = [{
    ...
    'DIRS': [BASE_DIR / 'templates'],
    ...
}]
```

---

## PHASE 3 — Models & Migrations

### Step 9: Build the Custom User Model

In `accounts/models.py`:

```python
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [('patient', 'Patient'), ('doctor', 'Doctor'), ('admin', 'Admin')]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='patient')
    phone = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def is_patient(self): return self.role == 'patient'
    def is_doctor(self): return self.role == 'doctor'
    def is_admin_user(self): return self.role == 'admin'
```

Create signals in `accounts/signals.py` to auto-create `PatientProfile` or `DoctorProfile` based on the user's role after registration.

### Step 10: Build All Remaining Models

In their respective app `models.py` files, create `PatientProfile`, `DoctorProfile`, `Consultation`, `Message`, `ConsultationImage`, and `Prescription` as designed in Step 4.

Run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## PHASE 4 — Authentication

### Step 11: Build Registration and Login

Create two registration forms:
- `PatientRegistrationForm` (extends `UserCreationForm`) — collects basic info
- `DoctorRegistrationForm` (extends `UserCreationForm`) — also collects license number, specialty, years of experience

Create views:
```
GET/POST  /accounts/register/patient/  → PatientRegistrationView
GET/POST  /accounts/register/doctor/   → DoctorRegistrationView
GET/POST  /accounts/login/             → Django LoginView (built-in)
POST      /accounts/logout/            → Django LogoutView (built-in)
```

After registration:
- Patients are immediately active and redirected to their dashboard
- Doctors are set as inactive (`is_verified=False`) and shown a "pending approval" message

### Step 12: Build Role-Based Access Control

Create three decorator/mixin functions to protect views:

```python
# accounts/decorators.py

def patient_required(view_func):
    # Redirect to login if not authenticated
    # Redirect to home if authenticated but not a patient
    ...

def doctor_required(view_func):
    # Also check that is_verified=True
    ...

def admin_required(view_func):
    ...
```

Apply these decorators to every protected view.

---

## PHASE 5 — Core App Views & Templates

### Step 13: Build the Patient Dashboard

**Views to create in `dashboard/views.py`:**

```
GET  /dashboard/patient/              → Patient home: stats + recent consultations
GET  /dashboard/patient/doctors/      → Browse available doctors
GET  /dashboard/patient/consult/new/  → New consultation request form
GET  /dashboard/patient/history/      → List of past consultations
```

**New Consultation Form:**
- `SymptomsDescriptionField` (Textarea)
- `DoctorSelectField` (dropdown of online/available doctors)
- `ImageUploadField` (multi-file image upload)
- On submit: create a `Consultation` object with `status='pending'`, save uploaded images to `ConsultationImage`

**Browse Doctors Page:**
- Render a grid of doctor cards using Tailwind
- Each card shows: profile picture, name, specialty, availability badge (green/grey/yellow dot), rating
- Filter form at the top: filter by specialty and availability status

---

### Step 14: Build the Doctor Dashboard

**Views to create:**

```
GET   /dashboard/doctor/              → Doctor home: queue count + next patient button
PATCH /dashboard/doctor/status/       → Toggle availability (AJAX POST)
POST  /dashboard/doctor/accept/       → Accept next consultation from queue
GET   /dashboard/doctor/history/      → Past consultations list
```

**Doctor Home Logic:**
- Query `Consultation.objects.filter(doctor=request.user, status='pending').order_by('created_at')`
- Display queue count prominently
- "Accept Next Patient" button submits a form that sets the oldest pending consultation to `status='active'` and redirects the doctor to the consultation room

---

### Step 15: Build the Consultation Room

This is the most critical view. Create it at:

```
GET /consultations/<int:pk>/room/  → ConsultationRoomView
```

**Template layout (split screen with Tailwind):**
- **Left panel (chat):** message history, image thumbnails inline, message input bar, attach image button, send button
- **Right panel (info):** patient profile details (doctor view) OR doctor info (patient view), uploaded images gallery with zoom

**Message loading:**
- On page load, fetch all existing `Message` objects for the consultation via a Django view and render them in the template
- New messages are pushed/received via WebSocket (Django Channels)

**Image upload in chat:**
- Separate AJAX `POST /consultations/<pk>/upload-image/` endpoint
- On success, broadcast the image URL over WebSocket so both parties see it immediately

**Consultation end:**
- Doctor clicks "End Consultation" → sets `status='completed'`, `ended_at=now()`
- Redirects doctor to prescription generation form
- Patient sees a "Consultation ended — your prescription will appear here" message

---

### Step 16: Build Django Channels WebSocket Consumer

Create `consultations/consumers.py`:

```python
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class ConsultationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.consultation_id = self.scope['url_route']['kwargs']['consultation_id']
        self.room_group_name = f'consultation_{self.consultation_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data.get('type')

        if event_type == 'chat_message':
            message = await self.save_message(data)
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'chat_message',
                'message': data['content'],
                'sender': data['sender'],
                'sent_at': str(message.sent_at),
            })

        elif event_type == 'typing':
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'typing_indicator',
                'sender': data['sender'],
                'is_typing': data['is_typing'],
            })

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def save_message(self, data):
        from consultations.models import Message, Consultation
        from accounts.models import User
        consultation = Consultation.objects.get(pk=self.consultation_id)
        sender = User.objects.get(pk=data['sender_id'])
        return Message.objects.create(
            consultation=consultation,
            sender=sender,
            message_type='text',
            content=data['content']
        )
```

Create `consultations/routing.py`:

```python
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/consultation/(?P<consultation_id>\d+)/$', consumers.ConsultationConsumer.as_asgi()),
]
```

---

### Step 17: Build the Chat Frontend with JavaScript

In the consultation room template, add a `<script>` block:

```javascript
const consultationId = "{{ consultation.id }}";
const currentUserId = "{{ request.user.id }}";
const currentUserName = "{{ request.user.get_full_name }}";

const socket = new WebSocket(`ws://${window.location.host}/ws/consultation/${consultationId}/`);

socket.onopen = () => console.log('WebSocket connected');

socket.onmessage = (e) => {
    const data = JSON.parse(e.data);
    if (data.type === 'chat_message') {
        appendMessage(data.sender, data.message, data.sent_at);
    } else if (data.type === 'typing_indicator') {
        showTypingIndicator(data.sender, data.is_typing);
    }
};

function sendMessage() {
    const input = document.getElementById('message-input');
    const content = input.value.trim();
    if (!content) return;
    socket.send(JSON.stringify({
        type: 'chat_message',
        content: content,
        sender: currentUserName,
        sender_id: currentUserId,
    }));
    input.value = '';
}

function appendMessage(sender, content, timestamp) {
    const messageList = document.getElementById('message-list');
    const div = document.createElement('div');
    const isSelf = (sender === currentUserName);
    div.className = `flex ${isSelf ? 'justify-end' : 'justify-start'} mb-2`;
    div.innerHTML = `
        <div class="${isSelf ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800'} 
                    rounded-lg px-4 py-2 max-w-xs shadow">
            <p class="text-xs font-bold mb-1">${isSelf ? 'You' : sender}</p>
            <p>${content}</p>
            <p class="text-xs opacity-60 mt-1">${timestamp}</p>
        </div>`;
    messageList.appendChild(div);
    messageList.scrollTop = messageList.scrollHeight;
}

// Typing indicator
let typingTimeout;
document.getElementById('message-input').addEventListener('input', () => {
    socket.send(JSON.stringify({ type: 'typing', sender: currentUserName, is_typing: true }));
    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(() => {
        socket.send(JSON.stringify({ type: 'typing', sender: currentUserName, is_typing: false }));
    }, 1500);
});
```

---

## PHASE 6 — Prescription Generation

### Step 18: Build the Prescription Form

Create a view at `GET/POST /prescriptions/create/<consultation_id>/` accessible only to doctors after ending a consultation.

**PrescriptionForm fields:**
- Medicines: use Django formset or a dynamic JavaScript table where the doctor can add rows (medicine name, dosage, frequency, duration)
- Notes (Textarea)
- Instructions (Textarea)

On form submission:
1. Save the `Prescription` object to the database
2. Call the PDF generation function
3. Save the PDF file to `MEDIA_ROOT/prescriptions/`
4. Store the file path in `prescription.pdf_file`
5. Redirect the doctor to the prescription detail view
6. Notify the patient (via a flag on the Consultation model that the template polls for)

---

### Step 19: Generate the PDF Prescription with ReportLab

Create `prescriptions/pdf.py`:

```python
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib import colors
import io

def generate_prescription_pdf(prescription):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)
    story = []
    styles = getSampleStyleSheet()

    # Header
    story.append(Paragraph("MediConnect — Digital Prescription", styles['Title']))
    story.append(Spacer(1, 12))

    # Doctor info
    doctor = prescription.doctor
    doctor_profile = doctor.doctorprofile
    story.append(Paragraph(f"Dr. {doctor.get_full_name()}", styles['Heading2']))
    story.append(Paragraph(f"Specialty: {doctor_profile.specialty}", styles['Normal']))
    story.append(Paragraph(f"License No: {doctor_profile.license_number}", styles['Normal']))
    story.append(Spacer(1, 12))

    # Patient info
    patient = prescription.patient
    story.append(Paragraph(f"Patient: {patient.get_full_name()}", styles['Normal']))
    story.append(Paragraph(f"Date Issued: {prescription.issued_at.strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Spacer(1, 20))

    # Medicines table
    data = [['Medicine', 'Dosage', 'Frequency', 'Duration']]
    for med in prescription.medicines:
        data.append([med['name'], med['dosage'], med['frequency'], med['duration']])

    table = Table(data, colWidths=[150, 100, 120, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563EB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#EFF6FF')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(table)
    story.append(Spacer(1, 20))

    # Notes
    if prescription.notes:
        story.append(Paragraph("Notes:", styles['Heading3']))
        story.append(Paragraph(prescription.notes, styles['Normal']))
        story.append(Spacer(1, 12))

    # Instructions
    if prescription.instructions:
        story.append(Paragraph("Instructions:", styles['Heading3']))
        story.append(Paragraph(prescription.instructions, styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer
```

In the view, after saving the `Prescription`, call this function and write the buffer to a `ContentFile` saved to `prescription.pdf_file`.

### Step 20: Build the Prescription Download View

```
GET /prescriptions/<int:pk>/download/  → Serve the PDF file as an attachment
```

```python
from django.http import FileResponse
from django.contrib.auth.decorators import login_required

@login_required
def download_prescription(request, pk):
    prescription = get_object_or_404(Prescription, pk=pk)
    # Ensure only the patient or doctor can download
    if request.user not in [prescription.patient, prescription.doctor]:
        return HttpForbidden()
    return FileResponse(prescription.pdf_file.open(), as_attachment=True,
                        filename=f'prescription_{prescription.id}.pdf')
```

---

## PHASE 7 — Admin Panel

### Step 21: Build the Admin Dashboard

Django's built-in `/admin/` panel can handle basic operations. Extend it for MediConnect:

**Register all models in `admin.py` of each app:**

```python
# accounts/admin.py
from django.contrib import admin
from .models import User, PatientProfile, DoctorProfile

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialty', 'license_number', 'is_verified']
    list_filter = ['is_verified', 'specialty']
    actions = ['approve_doctors']

    def approve_doctors(self, request, queryset):
        queryset.update(is_verified=True)
        # Also set user.is_active = True for each
    approve_doctors.short_description = "Approve selected doctors"
```

**Custom Admin Dashboard View** at `/dashboard/admin/`:

```
GET /dashboard/admin/           → Stats: total users, consultations today, pending doctors
GET /dashboard/admin/doctors/   → List all doctors with approve/reject buttons
GET /dashboard/admin/users/     → List all users with suspend/delete actions
```

---

## PHASE 8 — URL Configuration

### Step 22: Wire Up All URLs

**`mediconnect/urls.py`:**

```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('consultations/', include('consultations.urls')),
    path('prescriptions/', include('prescriptions.urls')),
    path('', include('dashboard.urls')),  # Home page
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**URL map summary:**

```
/                                    → Landing / Home page
/accounts/register/patient/          → Patient registration
/accounts/register/doctor/           → Doctor registration
/accounts/login/                     → Login
/accounts/logout/                    → Logout

/dashboard/patient/                  → Patient home
/dashboard/patient/doctors/          → Browse doctors
/dashboard/patient/consult/new/      → New consultation
/dashboard/patient/history/          → Consultation history

/dashboard/doctor/                   → Doctor home
/dashboard/doctor/status/            → Toggle availability (POST)
/dashboard/doctor/accept/            → Accept next patient (POST)
/dashboard/doctor/history/           → Past consultations

/dashboard/admin/                    → Admin stats
/dashboard/admin/doctors/            → Doctor management
/dashboard/admin/users/              → User management

/consultations/<pk>/room/            → Consultation chat room
/consultations/<pk>/upload-image/    → Image upload (AJAX POST)
/consultations/<pk>/end/             → End consultation (POST)

/prescriptions/create/<pk>/          → Create prescription form
/prescriptions/<pk>/                 → View prescription
/prescriptions/<pk>/download/        → Download PDF

ws/consultation/<pk>/                → WebSocket endpoint
```

---

## PHASE 9 — Premium Responsive UI Design System

MediConnect must feel like a world-class healthcare platform — not a student project. The design direction is **clinical luxury**: clean, trustworthy, and refined, with depth through subtle gradients, layered glass effects, and confident typography. Every screen must be fully responsive from mobile (320px) to ultra-wide (1920px+).

---

### Step 23: Define the Design System

Before building any template, establish the full design system as CSS custom properties. This ensures every page looks cohesive and every developer references the same tokens.

Add this to a `static/css/design-system.css` file and link it in `base.html`:

```css
/* ============================================
   MEDICONNECT DESIGN SYSTEM
   Direction: Clinical Luxury — trustworthy,
   refined, modern healthcare
   ============================================ */

@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

:root {
  /* ── Color Palette ── */
  --color-primary:        #0A6EBD;   /* Deep medical blue */
  --color-primary-light:  #3B9EE8;
  --color-primary-dark:   #064F8C;
  --color-accent:         #00C9A7;   /* Teal — vitality, health */
  --color-accent-warm:    #FF6B6B;   /* Coral — urgency, alerts */
  --color-accent-gold:    #F5A623;   /* Amber — warnings */

  --color-bg:             #F0F4F9;   /* Cool off-white background */
  --color-surface:        #FFFFFF;
  --color-surface-raised: #FFFFFF;
  --color-border:         rgba(10, 110, 189, 0.12);
  --color-border-strong:  rgba(10, 110, 189, 0.25);

  --color-text-primary:   #0D1B2A;   /* Near-black, not harsh */
  --color-text-secondary: #4A6785;
  --color-text-muted:     #8FA8C3;

  --color-success:        #10B981;
  --color-warning:        #F59E0B;
  --color-danger:         #EF4444;
  --color-online:         #10B981;
  --color-offline:        #94A3B8;
  --color-busy:           #F59E0B;

  /* ── Typography ── */
  --font-display:  'Sora', sans-serif;      /* Headlines, brand */
  --font-body:     'DM Sans', sans-serif;   /* All body text, UI */

  /* ── Spacing Scale ── */
  --space-xs:  0.25rem;
  --space-sm:  0.5rem;
  --space-md:  1rem;
  --space-lg:  1.5rem;
  --space-xl:  2rem;
  --space-2xl: 3rem;
  --space-3xl: 5rem;

  /* ── Border Radius ── */
  --radius-sm:   6px;
  --radius-md:   12px;
  --radius-lg:   20px;
  --radius-xl:   28px;
  --radius-full: 9999px;

  /* ── Shadows ── */
  --shadow-card:    0 2px 16px rgba(10, 110, 189, 0.08), 0 1px 4px rgba(0,0,0,0.04);
  --shadow-raised:  0 8px 32px rgba(10, 110, 189, 0.14), 0 2px 8px rgba(0,0,0,0.06);
  --shadow-modal:   0 24px 80px rgba(10, 110, 189, 0.2), 0 8px 24px rgba(0,0,0,0.1);
  --shadow-glow:    0 0 24px rgba(0, 201, 167, 0.35);

  /* ── Transitions ── */
  --transition-fast:   150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-normal: 250ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow:   400ms cubic-bezier(0.4, 0, 0.2, 1);

  /* ── Glass Effect ── */
  --glass-bg:     rgba(255, 255, 255, 0.72);
  --glass-border: rgba(255, 255, 255, 0.5);
  --glass-blur:   blur(16px);
}
```

---

### Step 24: Build the Premium Base Template

Replace the basic `base.html` with this production-grade template:

```html
<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}MediConnect{% endblock %}</title>

  <!-- Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap" rel="stylesheet">

  <!-- Icons -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">

  <!-- Tailwind -->
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            primary:  { DEFAULT: '#0A6EBD', light: '#3B9EE8', dark: '#064F8C' },
            accent:   { DEFAULT: '#00C9A7', warm: '#FF6B6B', gold: '#F5A623' },
            surface:  '#F0F4F9',
          },
          fontFamily: {
            display: ['Sora', 'sans-serif'],
            body:    ['DM Sans', 'sans-serif'],
          },
          borderRadius: {
            'xl': '20px',
            '2xl': '28px',
          },
          boxShadow: {
            'card':   '0 2px 16px rgba(10,110,189,0.08), 0 1px 4px rgba(0,0,0,0.04)',
            'raised': '0 8px 32px rgba(10,110,189,0.14), 0 2px 8px rgba(0,0,0,0.06)',
            'glow':   '0 0 24px rgba(0,201,167,0.35)',
          },
          backdropBlur: { glass: '16px' },
          animation: {
            'fade-in':   'fadeIn 0.4s ease-out forwards',
            'slide-up':  'slideUp 0.4s ease-out forwards',
            'pulse-dot': 'pulseDot 2s ease-in-out infinite',
          },
          keyframes: {
            fadeIn:   { from: { opacity: '0' }, to: { opacity: '1' } },
            slideUp:  { from: { opacity: '0', transform: 'translateY(16px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
            pulseDot: { '0%,100%': { transform: 'scale(1)', opacity: '1' }, '50%': { transform: 'scale(1.4)', opacity: '0.6' } },
          }
        }
      }
    }
  </script>

  <!-- Design System -->
  {% load static %}
  <link rel="stylesheet" href="{% static 'css/design-system.css' %}">

  <style>
    * { font-family: 'DM Sans', sans-serif; box-sizing: border-box; }
    h1,h2,h3,h4,h5 { font-family: 'Sora', sans-serif; }
    body { background-color: #F0F4F9; color: #0D1B2A; }

    /* Global mesh background */
    .mesh-bg {
      background:
        radial-gradient(ellipse at 0% 0%, rgba(10,110,189,0.08) 0%, transparent 60%),
        radial-gradient(ellipse at 100% 100%, rgba(0,201,167,0.06) 0%, transparent 60%),
        #F0F4F9;
    }

    /* Glass card utility */
    .glass-card {
      background: rgba(255,255,255,0.72);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid rgba(255,255,255,0.5);
      border-radius: 20px;
      box-shadow: 0 2px 16px rgba(10,110,189,0.08);
    }

    /* Premium card */
    .mc-card {
      background: #fff;
      border-radius: 20px;
      border: 1px solid rgba(10,110,189,0.1);
      box-shadow: 0 2px 16px rgba(10,110,189,0.08);
      transition: box-shadow 250ms ease, transform 250ms ease;
    }
    .mc-card:hover { box-shadow: 0 8px 32px rgba(10,110,189,0.14); transform: translateY(-2px); }

    /* Primary button */
    .btn-primary {
      display: inline-flex; align-items: center; gap: 8px;
      background: linear-gradient(135deg, #0A6EBD 0%, #3B9EE8 100%);
      color: #fff; font-weight: 600; font-family: 'Sora', sans-serif;
      padding: 12px 28px; border-radius: 9999px; border: none; cursor: pointer;
      box-shadow: 0 4px 16px rgba(10,110,189,0.3);
      transition: all 250ms ease;
    }
    .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(10,110,189,0.4); }
    .btn-primary:active { transform: translateY(0); }

    /* Secondary / outline button */
    .btn-secondary {
      display: inline-flex; align-items: center; gap: 8px;
      background: transparent; color: #0A6EBD;
      font-weight: 600; font-family: 'Sora', sans-serif;
      padding: 11px 28px; border-radius: 9999px;
      border: 2px solid rgba(10,110,189,0.3); cursor: pointer;
      transition: all 250ms ease;
    }
    .btn-secondary:hover { background: rgba(10,110,189,0.06); border-color: #0A6EBD; }

    /* Accent button */
    .btn-accent {
      background: linear-gradient(135deg, #00C9A7 0%, #00E5C4 100%);
      color: #fff; font-weight: 600; font-family: 'Sora', sans-serif;
      padding: 12px 28px; border-radius: 9999px; border: none; cursor: pointer;
      box-shadow: 0 4px 16px rgba(0,201,167,0.3);
      transition: all 250ms ease;
    }
    .btn-accent:hover { transform: translateY(-2px); box-shadow: 0 0 24px rgba(0,201,167,0.45); }

    /* Form inputs */
    .mc-input {
      width: 100%; padding: 14px 18px;
      background: #F0F4F9; border: 2px solid transparent;
      border-radius: 12px; font-size: 0.95rem; color: #0D1B2A;
      transition: all 200ms ease; outline: none;
    }
    .mc-input:focus { background: #fff; border-color: #0A6EBD; box-shadow: 0 0 0 4px rgba(10,110,189,0.1); }
    .mc-label { display: block; font-weight: 600; font-size: 0.85rem; color: #4A6785; margin-bottom: 6px; letter-spacing: 0.04em; text-transform: uppercase; }

    /* Status badge */
    .badge-online  { background: rgba(16,185,129,0.12); color: #059669; }
    .badge-offline { background: rgba(148,163,184,0.15); color: #64748B; }
    .badge-busy    { background: rgba(245,158,11,0.12); color: #D97706; }
    .status-badge  { display:inline-flex; align-items:center; gap:6px; padding:4px 12px; border-radius:9999px; font-size:0.78rem; font-weight:600; }

    /* Sidebar navigation */
    .sidebar-link {
      display: flex; align-items: center; gap: 12px;
      padding: 12px 16px; border-radius: 12px; color: #4A6785;
      font-weight: 500; text-decoration: none;
      transition: all 200ms ease;
    }
    .sidebar-link:hover { background: rgba(10,110,189,0.07); color: #0A6EBD; }
    .sidebar-link.active { background: linear-gradient(135deg,rgba(10,110,189,0.12),rgba(59,158,232,0.08)); color: #0A6EBD; font-weight: 600; }
    .sidebar-link .icon { width: 20px; text-align: center; }

    /* Animate on scroll (add class via JS) */
    .animate-on-scroll { opacity: 0; transform: translateY(20px); transition: opacity 0.5s ease, transform 0.5s ease; }
    .animate-on-scroll.visible { opacity: 1; transform: translateY(0); }

    /* Mobile nav overlay */
    .mobile-nav-open { overflow: hidden; }
  </style>

  {% block extra_head %}{% endblock %}
</head>

<body class="mesh-bg min-h-screen">

  <!-- ══ NAVBAR ══ -->
  <nav class="sticky top-0 z-50" style="background: rgba(255,255,255,0.82); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(10,110,189,0.1);">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">

      <!-- Logo -->
      <a href="/" class="flex items-center gap-2 text-primary-DEFAULT no-underline">
        <div class="w-9 h-9 rounded-xl flex items-center justify-center text-white text-lg"
             style="background: linear-gradient(135deg, #0A6EBD, #00C9A7);">
          <i class="fa-solid fa-stethoscope" style="font-size:16px;"></i>
        </div>
        <span style="font-family:'Sora',sans-serif; font-weight:700; font-size:1.2rem; color:#0D1B2A;">
          Medi<span style="color:#0A6EBD;">Connect</span>
        </span>
      </a>

      <!-- Desktop nav links -->
      <div class="hidden md:flex items-center gap-2">
        {% if user.is_authenticated %}
          <span class="text-sm text-gray-500 mr-2">{{ user.get_full_name }}</span>
          <a href="/dashboard/" class="sidebar-link py-2 px-4"><i class="fa-solid fa-grid-2 icon"></i> Dashboard</a>
          <a href="/accounts/logout/" class="btn-secondary py-2 px-5 text-sm">Sign Out</a>
        {% else %}
          <a href="/accounts/login/" class="sidebar-link py-2 px-4">Sign In</a>
          <a href="/accounts/register/patient/" class="btn-primary py-2 px-5 text-sm">Get Started</a>
        {% endif %}
      </div>

      <!-- Mobile hamburger -->
      <button id="mobile-menu-btn" class="md:hidden p-2 rounded-xl hover:bg-blue-50 transition-colors" onclick="toggleMobileNav()">
        <i class="fa-solid fa-bars text-gray-600 text-lg"></i>
      </button>
    </div>

    <!-- Mobile dropdown menu -->
    <div id="mobile-nav" class="hidden md:hidden px-4 pb-4 space-y-1 border-t border-blue-50 pt-3">
      {% if user.is_authenticated %}
        <p class="text-xs text-gray-400 px-3 pb-1">{{ user.get_full_name }}</p>
        <a href="/dashboard/" class="sidebar-link"><i class="fa-solid fa-grid-2 icon"></i> Dashboard</a>
        <a href="/accounts/logout/" class="sidebar-link text-red-500"><i class="fa-solid fa-right-from-bracket icon"></i> Sign Out</a>
      {% else %}
        <a href="/accounts/login/" class="sidebar-link"><i class="fa-solid fa-right-to-bracket icon"></i> Sign In</a>
        <a href="/accounts/register/patient/" class="sidebar-link"><i class="fa-solid fa-user-plus icon"></i> Register as Patient</a>
        <a href="/accounts/register/doctor/" class="sidebar-link"><i class="fa-solid fa-user-doctor icon"></i> Register as Doctor</a>
      {% endif %}
    </div>
  </nav>

  <!-- ══ FLASH MESSAGES ══ -->
  {% if messages %}
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4 space-y-2 animate-fade-in">
    {% for message in messages %}
    <div class="flex items-center gap-3 p-4 rounded-2xl text-sm font-medium
                {% if message.tags == 'error' %}bg-red-50 text-red-700 border border-red-200
                {% elif message.tags == 'success' %}bg-emerald-50 text-emerald-700 border border-emerald-200
                {% elif message.tags == 'warning' %}bg-amber-50 text-amber-700 border border-amber-200
                {% else %}bg-blue-50 text-blue-700 border border-blue-200{% endif %}">
      <i class="fa-solid {% if message.tags == 'error' %}fa-circle-exclamation{% elif message.tags == 'success' %}fa-circle-check{% elif message.tags == 'warning' %}fa-triangle-exclamation{% else %}fa-circle-info{% endif %}"></i>
      {{ message }}
    </div>
    {% endfor %}
  </div>
  {% endif %}

  <!-- ══ PAGE CONTENT ══ -->
  <main class="{% block main_class %}max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8{% endblock %}">
    {% block content %}{% endblock %}
  </main>

  <!-- ══ FOOTER ══ -->
  {% block footer %}
  <footer class="mt-16 border-t border-blue-100 py-8" style="background: rgba(255,255,255,0.6);">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row justify-between items-center gap-4 text-sm text-gray-400">
      <div class="flex items-center gap-2">
        <div class="w-6 h-6 rounded-lg flex items-center justify-center text-white text-xs"
             style="background: linear-gradient(135deg, #0A6EBD, #00C9A7);">
          <i class="fa-solid fa-stethoscope"></i>
        </div>
        <span style="font-family:'Sora',sans-serif; font-weight:600; color:#0D1B2A;">MediConnect</span>
      </div>
      <p>© {% now "Y" %} MediConnect. All rights reserved.</p>
      <div class="flex gap-4">
        <a href="#" class="hover:text-primary-DEFAULT transition-colors">Privacy</a>
        <a href="#" class="hover:text-primary-DEFAULT transition-colors">Terms</a>
        <a href="#" class="hover:text-primary-DEFAULT transition-colors">Support</a>
      </div>
    </div>
  </footer>
  {% endblock %}

  <!-- Global JS -->
  <script>
    // Mobile nav toggle
    function toggleMobileNav() {
      const nav = document.getElementById('mobile-nav');
      nav.classList.toggle('hidden');
    }

    // Animate on scroll
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
          setTimeout(() => entry.target.classList.add('visible'), i * 80);
        }
      });
    }, { threshold: 0.1 });
    document.querySelectorAll('.animate-on-scroll').forEach(el => observer.observe(el));

    // Staggered card entrance on page load
    document.querySelectorAll('[data-stagger]').forEach((el, i) => {
      el.style.animationDelay = `${i * 80}ms`;
      el.classList.add('animate-slide-up');
    });
  </script>

  {% block extra_scripts %}{% endblock %}
</body>
</html>
```

---

### Step 25: Design the Landing / Home Page

The landing page is the first impression — it must communicate trust and modernity instantly.

**Layout (full-width sections, no max-width container on hero):**

**Hero Section:**
- Full-viewport-height split layout: left = text, right = floating illustration/mockup
- Headline (Sora, 64px, bold): `"Healthcare at Your Fingertips"`
- Subtext (DM Sans, 20px, muted): one sentence explaining the platform
- Two CTAs side by side: `btn-primary` ("Get Started Free") + `btn-secondary` ("How It Works")
- Floating decorative elements: blurred teal circle (bottom-right), blue circle (top-left), subtle grid pattern overlay
- Background: deep blue-to-teal mesh gradient

**Stats Bar** (below hero, white glass card spanning full width):
- 3–4 stat counters: e.g. "10,000+ Patients" · "500+ Doctors" · "24/7 Available" · "98% Satisfaction"
- Each stat: large Sora number in primary blue, small DM Sans label below

**How It Works Section** (3 numbered steps with icons):
- Step 1: Register & Describe Symptoms
- Step 2: Connect with a Doctor Instantly
- Step 3: Receive Your Digital Prescription
- Each step: icon in gradient circle, headline, short description
- Animate cards on scroll with `animate-on-scroll` + stagger delay

**Browse Specialties Section:**
- Horizontal scrollable pill row of medical specialties (Cardiology, Dermatology, Pediatrics, etc.)
- Each pill: icon + label, hover lifts with shadow

**Testimonials Section:**
- 3-column card grid with patient quotes
- Each card: quote text, star rating (filled stars in accent gold), patient avatar initials circle, name

**Final CTA Banner:**
- Dark blue gradient background
- "Ready to consult a doctor?" headline
- Single large `btn-accent` button

---

### Step 26: Design the Authentication Pages

**Login Page:**
- Centered full-screen split: left half = decorative gradient panel with floating medical icons, right half = login form
- Form card: `glass-card` class, no visible border on inner, 48px padding
- Logo mark at top of form
- "Welcome back" in Sora 28px bold
- Email and password fields using `mc-input` class
- "Forgot password?" link aligned right in accent teal
- `btn-primary` full-width: "Sign In"
- Divider line: "or continue with" (for future OAuth)
- Bottom: "Don't have an account? Get Started" link
- Responsive: on mobile, hide the decorative left panel, show just the centered card

**Register Pages (Patient & Doctor):**
- Multi-step progress indicator at the top (Step 1: Account · Step 2: Profile · Step 3: Done)
- Patient step 1: name, email, password, confirm password
- Patient step 2: date of birth, gender, blood type, emergency contact
- Doctor step 1: name, email, password
- Doctor step 2: specialty (styled dropdown), license number, years of experience, short bio
- Each step transitions with a smooth slide animation
- Final step: animated success checkmark + "Pending Approval" notice for doctors

---

### Step 27: Design the Patient Dashboard

**Layout:**
- Collapsible left sidebar (240px wide on desktop, drawer on mobile)
- Main content area with generous padding

**Sidebar:**
- Logo at top
- User avatar (initials circle in gradient) + name + "Patient" role tag
- Navigation links using `sidebar-link` class:
  - 🏠 Home
  - 👨‍⚕️ Find a Doctor
  - 📋 My Consultations
  - 💊 Prescriptions
  - 👤 My Profile
- Sidebar collapses to icon-only on tablet (md breakpoint)
- On mobile: hidden by default, opens as a full-height drawer with overlay

**Main Content — Patient Home:**
- Greeting header: "Good morning, [Name] 👋" in Sora 28px
- Stats row (4 cards using `mc-card`, `data-stagger` attribute for entrance animation):
  - Total Consultations (blue icon)
  - Active Consultation (teal icon, pulses if one is active)
  - Prescriptions Received (amber icon)
  - Upcoming Scheduled (purple icon)
- Recent Consultations table:
  - Clean table with rounded corners, alternating subtle row backgrounds
  - Columns: Doctor, Specialty, Date, Status badge, Action button
  - Status badges: use color-coded pill badges (pending=amber, active=teal, completed=blue, cancelled=red)
  - Hover row highlights in very light blue

**Browse Doctors Page:**
- Search bar at top + filter dropdowns (Specialty, Availability) — all in one horizontal `glass-card` row
- Doctor grid: 3 columns desktop, 2 tablet, 1 mobile
- Doctor card (`mc-card`):
  - Top half: gradient header bar in specialty color, avatar circle centered overlapping the edge
  - Avatar: profile photo or initials in gradient circle
  - Name in Sora 16px bold
  - Specialty in muted DM Sans 13px
  - Availability badge (pulsing green dot for Online)
  - Star rating (filled gold stars)
  - Years of experience badge
  - Two buttons: "View Profile" (secondary) + "Consult Now" (primary, only shown if doctor is Online)
  - Card entrance animation staggered on load

---

### Step 28: Design the Doctor Dashboard

**Layout:** Same sidebar + main content structure as Patient Dashboard, but with doctor-specific navigation:
- 📊 Dashboard
- 👥 Patient Queue
- 💬 Active Consultation
- 📋 History
- 📝 Prescriptions
- 👤 Profile

**Doctor Home Panel:**

- **Availability Toggle** (top-right of header): large pill toggle switch — when clicked, sends AJAX POST and animates between Online (teal) / Offline (grey) / Busy (amber). Shows a pulsing dot next to current status.
- **Queue Counter Card**: oversized number in Sora 72px showing patients waiting, colored in primary blue. Below: "patients in queue". Animate the number when it changes.
- **"Accept Next Patient" Button**: full-width `btn-accent` with a stethoscope icon. Disabled and greyed out when queue is empty. When enabled, it pulses subtly.
- **Queue Preview** (below the button): mini list of next 3 patients in queue — name, symptom snippet, time waiting — each in a compact `mc-card`. This shows the doctor what's coming next without accepting yet.

---

### Step 29: Design the Consultation Room

This is the most used screen. It must be clean, distraction-free, and functional.

**Full-screen layout (no footer, minimal header):**

```
┌─────────────┬────────────────────────────────┐
│  Patient     │                                │
│  Info Panel  │         Chat Window            │
│  (300px)     │                                │
│              │  ┌─────────────────────────┐   │
│  · Name      │  │  Message bubbles        │   │
│  · Age       │  │  (scrollable)           │   │
│  · Symptoms  │  └─────────────────────────┘   │
│  · Images    │  ┌─────────────────────────┐   │
│              │  │  [📎] [Type message...] [▶]│   │
└─────────────┴──┴─────────────────────────┴──┘
```

On **mobile**: the info panel is hidden behind a toggle tab at the top. Chat takes full width.

**Chat Bubbles:**
- Patient messages: left-aligned, light grey bubble (`#F0F4F9`), patient name in small blue text above
- Doctor messages: right-aligned, gradient blue bubble (primary to primary-light), white text
- Timestamps: tiny muted text below each bubble
- Image messages: thumbnail with rounded corners, click to expand in a lightbox overlay
- "Typing..." indicator: three animated dots in a grey bubble

**Message Input Bar:**
- Sticky to bottom, `glass-card` style background
- Left: paperclip icon button for image upload (opens file picker)
- Center: expanding textarea (grows up to 4 lines, then scrolls)
- Right: teal send button (arrow icon), disabled when input is empty
- On image attach: show thumbnail preview strip above the input bar with remove (×) buttons

**Info Panel (Doctor View):**
- Patient avatar + name header
- Collapsible sections: "Symptoms", "Medical History", "Uploaded Images"
- Uploaded images: 2-column thumbnail grid, click to open lightbox
- "End Consultation" button: red outline button at the bottom of the panel, asks for confirmation in a modal before proceeding

**Lightbox / Image Viewer:**
- Dark overlay with blurred background
- Centered image with max 90vw / 90vh
- Close button (×) top right, keyboard ESC to close

---

### Step 30: Design the Prescription Pages

**Create Prescription Form (Doctor):**
- Clean single-column layout inside a `mc-card` with 40px padding
- "New Prescription" heading with doctor name and date pre-filled
- Patient info summary at the top (read-only, highlighted box)
- **Medicines Section:**
  - "Add Medicine" button adds a new row: [Medicine Name] [Dosage] [Frequency] [Duration] [🗑]
  - Each row is a compact horizontal flex layout with `mc-input` fields
  - Rows animate in with a slide-down effect when added
  - Drag handle to reorder rows (optional but premium touch)
- Notes and Instructions: full-width textarea with `mc-input` styling
- Submit button: `btn-primary` "Generate Prescription"

**Prescription Detail / Download Page:**
- Split layout: left = live preview of the prescription styled like a real medical document, right = action panel
- Preview card uses a white `mc-card` with subtle medical cross watermark in the background (CSS only, very faint)
- Header row: MediConnect logo + "Digital Prescription" label
- Doctor badge, patient badge side by side
- Medicines in a clean striped table
- Signature line at the bottom: doctor name with a line above it
- **Action Panel (right side, sticky):**
  - "Download PDF" — `btn-primary` with download icon
  - "Print" — `btn-secondary` with print icon
  - Consultation summary (date, doctor, patient)
- On mobile: actions move to a fixed bottom bar

---

### Step 31: Responsive Breakpoint Rules

Apply these Tailwind breakpoints consistently across every template:

| Breakpoint | Target | Key Layout Changes |
|---|---|---|
| default (< 640px) | Mobile phones | Single column, sidebar hidden, full-width cards, bottom action bars |
| `sm:` (640px+) | Large phones | 2-column grids allowed, slightly more padding |
| `md:` (768px+) | Tablets | Sidebar shown as icon-only, 2-col dashboards |
| `lg:` (1024px+) | Laptops | Full sidebar, 3-col doctor grid, side panels visible |
| `xl:` (1280px+) | Desktops | Max content width, generous padding |
| `2xl:` (1536px+) | Wide screens | Limit max-width to 1400px, centered |

**Mobile-specific rules:**
- All buttons minimum 44×44px touch targets
- No horizontal overflow — test every page at 320px width
- Sticky bottom action bars replace sidebar buttons on mobile for the consultation room and prescription page
- Navigation: hamburger drawer with full-height overlay and close button
- Doctor card grid: 1 column, full-width cards with horizontal layout (avatar left, info right)
- Chat room: input bar fixed to bottom of viewport, content scrolls behind it

---

### Step 32: UI Component Library

Build these reusable Django template partials in `templates/components/`:

**`_stat_card.html`** — Dashboard stat card with icon, number, label, and trend arrow

**`_doctor_card.html`** — Reusable doctor card for browse page and patient dashboard

**`_consultation_row.html`** — Table row for consultation history lists

**`_message_bubble.html`** — Individual chat message (text or image)

**`_status_badge.html`** — Availability/status pill badge with pulsing dot

**`_modal.html`** — Reusable confirmation modal with overlay

**`_empty_state.html`** — Illustrated empty state card (e.g., "No consultations yet") with a CTA button

**`_loading_spinner.html`** — Centered teal spinner for AJAX loading states

Include each component using Django's `{% include %}` tag:
```html
{% include 'components/_doctor_card.html' with doctor=doctor %}
```

---

### Step 33: Micro-Interactions & Animations

Add these polished details to elevate the feel from good to premium:

**Page Load:**
- `data-stagger` attribute on all dashboard cards → staggered `animate-slide-up` with 80ms delays
- Navbar fades in from top on first load

**Buttons:**
- All buttons: `transform hover:-translate-y-0.5 transition-all` — subtle lift on hover
- Primary buttons: box-shadow intensifies on hover
- Destructive actions (End Consultation, Delete): require a confirmation modal, button pulses red once when confirming

**Chat:**
- New message received: bubble slides in from the side
- Send button: short scale animation on click (0.95 → 1.05 → 1)
- Typing indicator: three dots bounce sequentially using CSS `animation-delay`

**Queue counter (Doctor Dashboard):**
- When the number changes, it does a quick scale-up + fade animation
- A subtle ping notification sound (optional, user must opt in)

**Form Fields:**
- Input focus: border transitions to primary blue + light blue outer ring (box-shadow)
- Validation errors: border turns red with a shake animation + red helper text fades in below

**Status Toggle:**
- Availability toggle pill slides with CSS transition, color changes smoothly
- The navbar status dot updates in real time via WebSocket event

**Image Upload:**
- Drag-and-drop zone: dashed border, highlights with teal glow on dragover
- After drop: image thumbnails animate in, progress bar fills while uploading

---

## PHASE 10 — Deployment on PythonAnywhere

### Step 25: Prepare for Production

Update `settings.py` for production:

```python
DEBUG = False
ALLOWED_HOSTS = ['yourusername.pythonanywhere.com']

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

Collect static files:

```bash
python manage.py collectstatic
```

### Step 26: Push to GitHub

```bash
git add .
git commit -m "Initial MediConnect project"
git push origin main
```

### Step 27: Set Up on PythonAnywhere

1. Log into [pythonanywhere.com](https://www.pythonanywhere.com) and open a **Bash console**
2. Clone your repository:
   ```bash
   git clone https://github.com/yourusername/mediconnect.git
   cd mediconnect
   ```
3. Create and activate a virtual environment:
   ```bash
   mkvirtualenv mediconnect --python=python3.11
   pip install -r requirements.txt
   ```
4. Run migrations and collect static files:
   ```bash
   python manage.py migrate
   python manage.py collectstatic
   python manage.py createsuperuser
   ```
5. Go to the **Web** tab in PythonAnywhere dashboard
6. Create a new web app → choose **Manual configuration** → **Python 3.11**
7. Set the **Source code** path to `/home/yourusername/mediconnect`
8. Set the **Virtualenv** path to `/home/yourusername/.virtualenvs/mediconnect`
9. Edit the **WSGI configuration file** — replace the contents with:
   ```python
   import os
   import sys
   path = '/home/yourusername/mediconnect'
   if path not in sys.path:
       sys.path.append(path)
   os.environ['DJANGO_SETTINGS_MODULE'] = 'mediconnect.settings'
   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```
10. Set up **Static Files** mapping in the Web tab:
    - URL: `/static/` → Directory: `/home/yourusername/mediconnect/staticfiles`
    - URL: `/media/` → Directory: `/home/yourusername/mediconnect/media`
11. Click **Reload** — your app is live

> **WebSocket note:** PythonAnywhere free accounts do not support WebSockets. If on a free account, replace the Django Channels consumer with an AJAX polling fallback that fetches `/consultations/<pk>/messages/` every 2 seconds using `setInterval`. Paid accounts support ASGI/Daphne and full WebSocket connections.

### Step 28: Set Up a Secret Key and Environment Variables

On PythonAnywhere, store secrets in the WSGI file or use a `.env` file with `python-dotenv`:

```python
# In your WSGI file or settings.py
import os
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'fallback-dev-key')
```

Set environment variables in the PythonAnywhere **Web tab → Environment variables** section.

---

## PHASE 11 — Testing

### Step 29: Write Django Tests

Create `tests.py` in each app. Use Django's built-in `TestCase`:

**Authentication Tests** (`accounts/tests.py`)
- Patient can register and is assigned `role='patient'`
- Doctor registers and `is_verified=False` by default
- Login returns a valid session
- Patient cannot access doctor-only views
- Doctor cannot access admin views

**Consultation Tests** (`consultations/tests.py`)
- Patient can create a consultation request
- Consultation starts with `status='pending'`
- Doctor accepts → `status='active'`
- Message is saved when sent through WebSocket consumer
- Image uploads are saved and linked to the correct consultation

**Prescription Tests** (`prescriptions/tests.py`)
- Prescription is created and linked to the correct consultation
- PDF is generated and saved to the `pdf_file` field
- Only the patient and doctor involved can download the PDF

**Run all tests:**
```bash
python manage.py test
```

---

## PHASE 12 — Future Enhancements (Roadmap)

After v1.0 is live on PythonAnywhere, consider:

- **Upgrade to PostgreSQL** on a paid PythonAnywhere plan for better concurrent read/write performance
- **Redis Channel Layer** for reliable multi-instance WebSocket support
- **Video Consultations** via Daily.co or Twilio Video (embeds via iframe)
- **Email Notifications** using Django's `send_mail` with PythonAnywhere's SMTP allowlist
- **Doctor Rating System** — patients rate after consultation ends
- **Appointment Scheduling** — calendar-based booking instead of live queue only
- **AI Symptom Pre-screening** — integrate with an LLM API before patient reaches doctor
- **Mobile Responsiveness Improvements** — enhanced Tailwind breakpoints for small screens
- **Audit Logging** — log every data access event for compliance

---

## Deliverables Summary

| Deliverable | Description |
|---|---|
| Django Project | Fully structured multi-app Django project |
| Custom User Model | Extended AbstractUser with role-based access |
| Database Models | All 7 models migrated and working with SQLite |
| Auth System | Registration (patient/doctor), login, role guards |
| Patient Dashboard | Browse doctors, request consultation, view history |
| Doctor Dashboard | Queue management, availability toggle, consultation room |
| Admin Dashboard | Doctor approval, user management, stats |
| Real-Time Chat | Django Channels WebSocket consumer + JS frontend |
| Image Upload | AJAX upload endpoint, inline display in chat |
| Prescription Engine | ReportLab PDF generation with download view |
| Design System | CSS custom properties for colors, typography, spacing, shadows, and animations |
| Premium Base Template | Glass navbar, mesh backgrounds, Font Awesome icons, Sora + DM Sans fonts |
| Responsive UI | All pages tested from 320px mobile to 1920px desktop |
| Component Library | 8+ reusable Django template partials (cards, modals, badges, empty states) |
| Landing Page | Hero, stats bar, how-it-works, testimonials, CTA sections |
| Auth Pages | Split-screen login, multi-step registration with progress indicator |
| Patient Dashboard | Sidebar layout, stats cards, doctor grid, consultation history |
| Doctor Dashboard | Queue counter, availability toggle, queue preview cards |
| Consultation Room | Split-screen chat, image lightbox, typing indicator, sticky input bar |
| Prescription Pages | Live preview card, action panel, printable layout |
| Micro-Interactions | Stagger animations, hover lifts, form transitions, drag-and-drop upload |
| PythonAnywhere Deploy | Live WSGI deployment with static/media file serving |
| Test Suite | Django TestCase tests for all major features |
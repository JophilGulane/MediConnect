# AGENT.md — MediConnect

> This file is the authoritative guide for any AI coding agent working on this project.
> Read this file **in full** before writing, editing, or deleting any code.

---

## 1. Project Identity

| Field | Value |
|---|---|
| **Project Name** | MediConnect |
| **Type** | E-Consultation / Telemedicine Web Application |
| **Purpose** | Connect patients to doctors for online consultation, image sharing, real-time chat, and digital prescriptions |
| **Deployment** | PythonAnywhere |
| **Django Version** | 4.x |
| **Python Version** | 3.11 |

---

## 2. Repository Structure

```
mediconnect/                        ← Project root
│
├── AGENT.md                        ← You are here
├── manage.py
├── requirements.txt
├── db.sqlite3                      ← Never commit this
├── .env                            ← Never commit this
├── .gitignore
│
├── mediconnect/                    ← Django project config
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py                     ← Django Channels entry point
│   └── wsgi.py                     ← PythonAnywhere entry point
│
├── accounts/                       ← Custom User model, auth, profiles
│   ├── models.py                   ← User, PatientProfile, DoctorProfile
│   ├── views.py                    ← Register, login, profile views
│   ├── forms.py                    ← Registration and profile forms
│   ├── decorators.py               ← patient_required, doctor_required, admin_required
│   ├── signals.py                  ← Auto-create profiles on user save
│   ├── urls.py
│   ├── admin.py
│   └── tests.py
│
├── consultations/                  ← Consultation requests, chat, images
│   ├── models.py                   ← Consultation, Message, ConsultationImage
│   ├── views.py                    ← Room view, queue logic, image upload
│   ├── consumers.py                ← Django Channels WebSocket consumer
│   ├── routing.py                  ← WebSocket URL routing
│   ├── forms.py
│   ├── urls.py
│   ├── admin.py
│   └── tests.py
│
├── prescriptions/                  ← Prescription creation and PDF generation
│   ├── models.py                   ← Prescription model
│   ├── views.py                    ← Create, detail, download views
│   ├── forms.py                    ← PrescriptionForm with dynamic medicine rows
│   ├── pdf.py                      ← ReportLab PDF generation logic
│   ├── urls.py
│   ├── admin.py
│   └── tests.py
│
├── dashboard/                      ← Role-based dashboards and landing page
│   ├── views.py                    ← Patient, Doctor, Admin dashboard views
│   ├── urls.py
│   └── tests.py
│
├── templates/                      ← All Django HTML templates
│   ├── base.html                   ← Master layout (navbar, footer, design system)
│   ├── home.html                   ← Public landing page
│   ├── components/                 ← Reusable partials ({% include %})
│   │   ├── _stat_card.html
│   │   ├── _doctor_card.html
│   │   ├── _consultation_row.html
│   │   ├── _message_bubble.html
│   │   ├── _status_badge.html
│   │   ├── _modal.html
│   │   ├── _empty_state.html
│   │   └── _loading_spinner.html
│   ├── accounts/
│   │   ├── login.html
│   │   ├── register_patient.html
│   │   └── register_doctor.html
│   ├── dashboard/
│   │   ├── patient_home.html
│   │   ├── doctor_home.html
│   │   ├── admin_home.html
│   │   ├── browse_doctors.html
│   │   └── admin_users.html
│   ├── consultations/
│   │   ├── room.html               ← The real-time chat room
│   │   └── history.html
│   └── prescriptions/
│       ├── create.html
│       ├── detail.html
│       └── download_redirect.html
│
├── static/
│   ├── css/
│   │   └── design-system.css       ← CSS custom properties and global utility classes
│   ├── js/
│   │   └── chat.js                 ← WebSocket chat logic (extracted from template)
│   └── images/
│       └── logo.svg
│
└── media/                          ← User-uploaded files (gitignored)
    ├── profile_pics/
    ├── consultation_images/
    └── prescriptions/
```

---

## 3. Core Commands

Always run these from the project root with the virtual environment activated.

```bash
# Activate virtual environment
source venv/bin/activate            # Linux/macOS
venv\Scripts\activate               # Windows

# Run development server (HTTP only — no WebSockets)
python manage.py runserver

# Run with Daphne (ASGI — required for WebSockets)
daphne -b 127.0.0.1 -p 8000 mediconnect.asgi:application

# Database
python manage.py makemigrations     # After any model change
python manage.py migrate            # Apply migrations
python manage.py showmigrations     # Check migration state

# Create superuser (admin)
python manage.py createsuperuser

# Collect static files (before deploying)
python manage.py collectstatic --noinput

# Run all tests
python manage.py test

# Run tests for a specific app
python manage.py test accounts
python manage.py test consultations
python manage.py test prescriptions

# Run tests with verbosity
python manage.py test --verbosity=2

# Open Django shell
python manage.py shell

# Install dependencies
pip install -r requirements.txt

# Freeze current dependencies
pip freeze > requirements.txt
```

---

## 4. Environment Variables

Never hardcode secrets. All sensitive values live in a `.env` file (gitignored). The agent must always load settings via `os.environ.get(...)` with safe fallbacks for development only.

```env
# .env — DO NOT COMMIT
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,yourusername.pythonanywhere.com

# Email (for prescription delivery)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=MediConnect <noreply@mediconnect.com>

# File storage
MEDIA_ROOT=media/
MAX_UPLOAD_SIZE_MB=5
```

Load in `settings.py` using:
```python
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'unsafe-dev-key-change-in-prod')
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost').split(',')
```

---

## 5. Data Models Reference

### 5.1 User Roles

Every `User` has a `role` field. All role checks must use the model's helper methods, never raw string comparisons in views.

```python
user.is_patient()       # role == 'patient'
user.is_doctor()        # role == 'doctor'
user.is_admin_user()    # role == 'admin'
```

### 5.2 Model Relationships

```
User (1) ──── (1) PatientProfile
User (1) ──── (1) DoctorProfile
User (1) ──── (N) Consultation [as patient]
User (1) ──── (N) Consultation [as doctor]
Consultation (1) ──── (N) Message
Consultation (1) ──── (N) ConsultationImage
Consultation (1) ──── (1) Prescription
```

### 5.3 Status Enums

**Consultation.status:**
- `pending` — patient submitted, waiting for doctor to accept
- `active` — doctor accepted, chat is live
- `completed` — doctor clicked "End Consultation"
- `cancelled` — patient cancelled before doctor accepted

**DoctorProfile.availability_status:**
- `online` — accepting new consultations
- `busy` — in an active consultation
- `offline` — not accepting requests

### 5.4 Message.message_type

- `text` — content field is plain text
- `image` — content field is a relative URL to `media/consultation_images/`

---

## 6. URL Map

```
/                                         home (landing page)
/accounts/register/patient/               PatientRegistrationView
/accounts/register/doctor/                DoctorRegistrationView
/accounts/login/                          Django LoginView
/accounts/logout/                         Django LogoutView
/accounts/profile/                        ProfileView (edit own profile)

/dashboard/                               Redirects based on role
/dashboard/patient/                       Patient home [patient_required]
/dashboard/patient/doctors/               Browse doctors [patient_required]
/dashboard/patient/consult/new/           New consultation form [patient_required]
/dashboard/patient/history/               Patient consultation history [patient_required]
/dashboard/doctor/                        Doctor home [doctor_required + is_verified]
/dashboard/doctor/status/                 Toggle availability (POST only) [doctor_required]
/dashboard/doctor/accept/                 Accept next patient (POST only) [doctor_required]
/dashboard/doctor/history/                Doctor past consultations [doctor_required]
/dashboard/admin/                         Admin stats [admin_required]
/dashboard/admin/doctors/                 Doctor approval list [admin_required]
/dashboard/admin/doctors/<id>/verify/     Approve doctor (POST) [admin_required]
/dashboard/admin/doctors/<id>/reject/     Reject doctor (POST) [admin_required]
/dashboard/admin/users/                   User list [admin_required]

/consultations/<pk>/room/                 Consultation chat room [login_required]
/consultations/<pk>/messages/             Fetch messages (AJAX GET) [login_required]
/consultations/<pk>/upload-image/         Upload image (AJAX POST) [login_required]
/consultations/<pk>/end/                  End consultation (POST) [doctor_required]

/prescriptions/create/<consultation_pk>/  Create prescription [doctor_required]
/prescriptions/<pk>/                      View prescription [login_required]
/prescriptions/<pk>/download/             Download PDF [login_required]

ws/consultation/<pk>/                     WebSocket endpoint (Django Channels)

/admin/                                   Django built-in admin panel
```

---

## 7. Access Control Rules

Never bypass these rules. Apply the correct decorator/mixin to every single view.

| View | Decorator / Mixin |
|---|---|
| Patient dashboard views | `@patient_required` |
| Doctor dashboard views | `@doctor_required` (also checks `is_verified=True`) |
| Admin dashboard views | `@admin_required` |
| Consultation room | `@login_required` + ownership check (patient or doctor of that consultation) |
| Prescription download | `@login_required` + ownership check (only the patient or doctor involved) |
| Image upload | `@login_required` + participant check |
| WebSocket connection | JWT or session in Channels `AuthMiddlewareStack` |

**Ownership check pattern:**
```python
consultation = get_object_or_404(Consultation, pk=pk)
if request.user not in [consultation.patient, consultation.doctor]:
    raise PermissionDenied
```

---

## 8. Coding Conventions

### 8.1 General

- **Python:** Follow PEP 8. Max line length 100 characters.
- **Django:** Class-based views preferred for CRUD; function-based views acceptable for simple or AJAX endpoints.
- **Never** put business logic inside templates. Keep templates dumb — only display data.
- **Never** put complex queries inside templates. Do all DB work in views or model managers.
- All model methods that touch the DB must be in `models.py` or a `services.py` file, not in views.

### 8.2 Views

```python
# Preferred pattern for protected views
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from accounts.decorators import patient_required

@method_decorator(patient_required, name='dispatch')
class PatientHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/patient_home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['consultations'] = Consultation.objects.filter(
            patient=self.request.user
        ).select_related('doctor', 'doctor__doctorprofile').order_by('-created_at')[:10]
        return ctx
```

### 8.3 Models

- Always define `__str__` on every model.
- Always define `class Meta` with at minimum `ordering` and `verbose_name`.
- Use `select_related` and `prefetch_related` everywhere. Never allow N+1 queries.
- Never use `objects.all()` without a filter in production views — always paginate or limit.

```python
class Consultation(models.Model):
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Consultation'
        verbose_name_plural = 'Consultations'

    def __str__(self):
        return f"Consultation #{self.pk} — {self.patient} with Dr. {self.doctor}"
```

### 8.4 Templates

- All templates extend `templates/base.html` using `{% extends 'base.html' %}`.
- Reusable UI elements live in `templates/components/` and are included with `{% include %}`.
- Pass explicit variables to includes: `{% include 'components/_doctor_card.html' with doctor=doctor only %}`.
- Never write inline `<style>` blocks in templates. All styles go in `design-system.css` or Tailwind utility classes.
- Never write `<script>` blocks with business logic in templates. Extract to `static/js/` files.
- The one exception: the WebSocket connection setup script in `consultations/room.html` may remain inline as it requires Django template variables (consultation ID, user ID).

### 8.5 Forms

- All forms must use `{% csrf_token %}`.
- Apply `mc-input` CSS class to all form input fields via `widget_tweaks`:
  ```html
  {% load widget_tweaks %}
  {{ form.email|add_class:"mc-input" }}
  ```
- Show field errors below each input using `{{ form.field.errors }}`.
- Show non-field errors at the top of the form.

### 8.6 AJAX Endpoints

- All AJAX POST endpoints must verify `request.headers.get('X-Requested-With') == 'XMLHttpRequest'` or check `Content-Type: application/json`.
- Always return JSON responses: `JsonResponse({'status': 'ok', 'data': ...})`.
- On error: `JsonResponse({'status': 'error', 'message': '...'}, status=400)`.
- Include `csrftoken` cookie in all AJAX requests from the frontend.

### 8.7 WebSocket Consumer

- The `ConsultationConsumer` in `consultations/consumers.py` must be `AsyncWebsocketConsumer`.
- All DB operations inside the consumer must use `@database_sync_to_async`.
- The room group name format is: `consultation_{consultation_id}` — never deviate from this.
- Validate that the connecting user is a participant of the consultation on `connect()`. Reject unauthorized connections.

```python
async def connect(self):
    self.consultation_id = self.scope['url_route']['kwargs']['consultation_id']
    user = self.scope['user']
    # Validate participation
    is_participant = await self.check_participant(user, self.consultation_id)
    if not is_participant:
        await self.close(code=4003)
        return
    self.room_group_name = f'consultation_{self.consultation_id}'
    await self.channel_layer.group_add(self.room_group_name, self.channel_name)
    await self.accept()
```

---

## 9. Design System Rules

The agent must follow the design system exactly. Do not deviate from these rules when writing or modifying templates.

### 9.1 Fonts

- **Headlines (h1–h5), brand text, buttons:** `font-family: 'Sora', sans-serif`
- **All body text, labels, inputs, paragraphs:** `font-family: 'DM Sans', sans-serif`
- Never use Arial, Roboto, Inter, or system-ui.

### 9.2 Color Usage

| Use Case | Value |
|---|---|
| Primary actions, links, active states | `#0A6EBD` (primary blue) |
| Success, online status, accent CTA | `#00C9A7` (teal) |
| Warnings, busy status | `#F5A623` (amber) |
| Errors, danger, cancel | `#EF4444` (red) |
| Page background | `#F0F4F9` (cool off-white) |
| Card surfaces | `#FFFFFF` |
| Primary text | `#0D1B2A` |
| Secondary text | `#4A6785` |
| Muted / placeholder text | `#8FA8C3` |

Never use arbitrary hex values that are not in this palette. If a new color is needed, add it to `design-system.css` as a CSS variable first, then use it.

### 9.3 Spacing

Use Tailwind's spacing scale. Prefer multiples of 4 (p-4, p-8, gap-6, etc.). Minimum card padding is `p-6` on mobile, `p-8` on desktop (`lg:p-8`).

### 9.4 Buttons

Always use one of the three button classes from `design-system.css`:
- `.btn-primary` — primary gradient, for main CTAs
- `.btn-secondary` — outline style, for secondary actions
- `.btn-accent` — teal gradient, for affirmative / success actions (e.g., "Accept Patient")

Never create ad-hoc button styles. Never use bare Tailwind classes for buttons.

### 9.5 Cards

Use `.mc-card` for all content cards. Use `.glass-card` only for overlay elements, navbars, and modals. Never use plain `<div class="bg-white rounded shadow">` without these classes.

### 9.6 Responsive Rules

Every template must work at all four breakpoints. Test at 375px (mobile), 768px (tablet), 1024px (laptop), and 1280px (desktop) minimum.

- Sidebars: hidden on mobile (drawer), icon-only on `md:`, full on `lg:`
- Doctor grid: 1 col mobile, 2 col `sm:`, 3 col `lg:`
- Consultation room info panel: hidden on mobile (toggle tab), visible on `lg:`
- Minimum touch target size: 44×44px for all buttons and interactive elements

---

## 10. Database Rules

- **Never** delete migration files. If a migration is broken, fix it; don't delete it.
- **Never** edit an existing migration that has already been applied. Create a new one.
- After every `models.py` change, run `makemigrations` immediately, review the generated file, then run `migrate`.
- For every new model field added to an existing model, provide a default value or `null=True, blank=True` to avoid breaking existing migrations.
- Use `select_related` whenever accessing a ForeignKey or OneToOneField across a queryset.
- Use `prefetch_related` for ManyToMany or reverse ForeignKey access.
- Limit list queries to a maximum of 100 rows. Use Django's `Paginator` for all list views.

---

## 11. File Upload Rules

- Allowed types: `image/jpeg`, `image/png`, `image/webp` only.
- Maximum file size: 5MB per file. Validate on both client (JS file size check before upload) and server (view-level validation).
- Validate MIME type on the server using Python's `imghdr` or `Pillow` — never trust the file extension alone.
- Save all consultation images to `media/consultation_images/<consultation_id>/`.
- Save profile pictures to `media/profile_pics/<user_id>/`.
- Save generated prescription PDFs to `media/prescriptions/<prescription_id>/`.
- Never serve media files directly in development via Django in production — on PythonAnywhere, media files are served via the static file mapping in the Web tab.

---

## 12. PDF Generation Rules

All prescription PDFs are generated in `prescriptions/pdf.py` using ReportLab.

- Never generate PDFs in a template or view directly. Always call `generate_prescription_pdf(prescription)` from `pdf.py`.
- The function returns a `BytesIO` buffer. Save it to the model's `FileField` using `ContentFile`.
- PDF contents must always include: doctor name, license number, specialty, patient name, date issued, medicines table, notes, instructions.
- Use the color `#0A6EBD` for table headers and `#EFF6FF` for alternating row backgrounds to match the design system.
- After generating and saving the PDF, the view must redirect the doctor to `/prescriptions/<pk>/` — never serve the PDF directly from the creation view.

---

## 13. Testing Requirements

Every new feature must have corresponding tests before the feature is considered done.

### 13.1 What to Test

**accounts/tests.py**
- Patient registration creates a `PatientProfile` automatically
- Doctor registration sets `is_verified=False`
- Login with correct credentials returns HTTP 302 redirect
- Login with wrong credentials returns HTTP 200 with error
- `@patient_required` decorator returns 403 for a doctor user
- `@doctor_required` decorator returns 403 for a patient user and for an unverified doctor

**consultations/tests.py**
- A patient can create a consultation (POST to new consultation URL)
- New consultation has `status='pending'`
- Doctor can accept a consultation → `status='active'`
- Patient cannot accept a consultation
- Doctor ending consultation sets `status='completed'` and `ended_at` is not null
- Message is saved to the DB when `ConsultationConsumer.receive()` is called
- Image upload endpoint rejects files over 5MB
- Image upload endpoint rejects non-image MIME types
- Unauthorized user cannot access the consultation room (HTTP 403)

**prescriptions/tests.py**
- Doctor can create a prescription linked to a completed consultation
- `generate_prescription_pdf()` returns a non-empty `BytesIO` object
- Download view returns HTTP 200 with `Content-Type: application/pdf` for the involved patient
- Download view returns HTTP 403 for a user not involved in the consultation
- A prescription cannot be created for a consultation with `status != 'completed'`

### 13.2 Test Conventions

```python
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User, DoctorProfile, PatientProfile

class ConsultationTests(TestCase):
    def setUp(self):
        # Create test users in setUp, not in the test itself
        self.patient = User.objects.create_user(
            username='patient1', email='patient@test.com',
            password='testpass123', role='patient'
        )
        self.doctor_user = User.objects.create_user(
            username='doctor1', email='doctor@test.com',
            password='testpass123', role='doctor'
        )
        self.doctor_profile = DoctorProfile.objects.create(
            user=self.doctor_user, specialty='General', 
            license_number='LIC001', is_verified=True,
            availability_status='online'
        )
        self.client = Client()

    def test_patient_can_create_consultation(self):
        self.client.login(username='patient1', password='testpass123')
        response = self.client.post(reverse('new_consultation'), {
            'doctor': self.doctor_user.pk,
            'symptoms_description': 'I have a headache'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Consultation.objects.count(), 1)
        self.assertEqual(Consultation.objects.first().status, 'pending')
```

---

## 14. Deployment Checklist (PythonAnywhere)

Run through this checklist in order before every production deployment.

- [ ] `DEBUG = False` in settings (loaded from `.env`)
- [ ] `ALLOWED_HOSTS` includes `yourusername.pythonanywhere.com`
- [ ] `SECRET_KEY` is set from environment variable, not hardcoded
- [ ] `SECURE_SSL_REDIRECT = True`
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] `python manage.py collectstatic --noinput` has been run
- [ ] `python manage.py migrate` has been run
- [ ] Static files mapping set in PythonAnywhere Web tab: `/static/` → `...mediconnect/staticfiles/`
- [ ] Media files mapping set in PythonAnywhere Web tab: `/media/` → `...mediconnect/media/`
- [ ] WSGI configuration file points to `mediconnect.wsgi:application`
- [ ] Virtual environment path set correctly in PythonAnywhere Web tab
- [ ] All environment variables set in PythonAnywhere Web tab → Environment Variables section
- [ ] `db.sqlite3` exists and is writable by the PythonAnywhere process
- [ ] `media/` directory exists and is writable
- [ ] Click **Reload** on the Web tab after every code change or `git pull`

---

## 15. Common Pitfalls — Do Not Repeat These

| Mistake | Correct Approach |
|---|---|
| Using `localStorage` for auth tokens | Use Django's session-based auth only |
| Checking role with `user.role == 'doctor'` in views | Use `user.is_doctor()` helper method |
| Serving the WebSocket on the same port as WSGI in production | Use Daphne separately; PythonAnywhere routes WS traffic on paid plans |
| Using `WidthType.PERCENTAGE` in tables (N/A here — no docx) | — |
| Creating migrations by hand | Always use `python manage.py makemigrations` |
| Deleting and re-creating the SQLite database to fix migration issues | Fix the migration properly; never drop prod data |
| Importing from `consultations.models` inside `accounts/models.py` | Causes circular imports — use string references or move shared logic to a `core` app |
| Using `request.user` in a signal | Signals don't have access to the request; pass data through the model or use middleware |
| Committing `.env` or `db.sqlite3` to git | Both are in `.gitignore` — never force-add them |
| Putting all apps' URLs in `mediconnect/urls.py` directly | Each app has its own `urls.py`; include them with `include()` |
| Running `collectstatic` without `--noinput` in automated scripts | Always use `--noinput` to prevent interactive prompts hanging the script |
| Writing CSS in `<style>` tags in individual templates | All styles go in `static/css/design-system.css` or as Tailwind classes |
| Using hardcoded `/media/` paths in templates | Always use `{{ object.image.url }}` or `{% get_media_prefix %}` |
| N+1 queries in list views | Always use `select_related` / `prefetch_related` |
| Forgetting `{% csrf_token %}` in any POST form | Every form, every time |
| Writing business logic in templates | Logic belongs in views, model methods, or services — never in templates |

---

## 16. Git Workflow

```bash
# Branch naming
feature/patient-dashboard
feature/consultation-chat
feature/prescription-pdf
fix/doctor-queue-ordering
fix/image-upload-validation
chore/add-tests-consultations

# Commit message format
feat: add doctor availability toggle with AJAX
fix: prevent unauthorized users from joining consultation rooms
test: add prescription download access control tests
style: apply mc-card class to doctor browse grid
docs: update AGENT.md with WebSocket validation rules
refactor: extract PDF generation into prescriptions/pdf.py

# Before every commit
python manage.py test          # All tests must pass
python manage.py migrate       # No unapplied migrations
# Review any new/changed files with git diff --stat
```

---

## 17. Key Dependencies

```
# requirements.txt
django>=4.2,<5.0
channels>=4.0
daphne>=4.0
pillow>=10.0                   # Image field support + MIME validation
reportlab>=4.0                 # PDF prescription generation
django-crispy-forms>=2.0
crispy-tailwind>=0.5
django-widget-tweaks>=1.5
python-dotenv>=1.0
```

Install with:
```bash
pip install -r requirements.txt
```

---

## 18. Glossary

| Term | Meaning in this project |
|---|---|
| **Consultation** | A single patient-doctor session (request → chat → prescription) |
| **Queue** | The ordered list of `pending` consultations for a specific doctor |
| **Room** | The real-time chat page for an active consultation |
| **Consumer** | The Django Channels WebSocket handler in `consultations/consumers.py` |
| **Channel Layer** | The in-memory (dev) or Redis (prod) pub/sub layer for WebSocket messaging |
| **Participant** | Either the patient or the doctor belonging to a specific consultation |
| **Verified Doctor** | A doctor whose `DoctorProfile.is_verified == True` (set by admin) |
| **Design System** | The CSS token file at `static/css/design-system.css` |
| **mc-card** | The standard card CSS class — white surface, rounded-xl, shadow-card |
| **glass-card** | Frosted-glass card variant for navbars, modals, and overlays |
| **btn-primary / secondary / accent** | The three allowed button variants — never create ad-hoc button styles |
| **AJAX endpoint** | A Django view that returns `JsonResponse` instead of an HTML page |
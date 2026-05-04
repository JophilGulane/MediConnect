from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from accounts.decorators import patient_required, doctor_required, admin_required
from accounts.models import User, DoctorProfile
from consultations.models import Consultation
from consultations.forms import NewConsultationForm


@login_required
def home(request):
    """Redirect to the appropriate dashboard based on user role."""
    user = request.user
    if user.is_superuser or user.is_admin_user():
        return redirect('dashboard:admin_home')
    elif user.is_patient():
        return redirect('dashboard:patient_home')
    elif user.is_doctor():
        if not user.doctorprofile.is_verified:
            return redirect('accounts:doctor_pending')
        return redirect('dashboard:doctor_home')
    return redirect('dashboard:landing')


def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    return render(request, 'home.html')


# ─────────────────────── PATIENT VIEWS ──────────────────────────

@patient_required
def patient_home(request):
    consultations = Consultation.objects.filter(
        patient=request.user
    ).select_related('doctor', 'doctor__doctorprofile').order_by('-created_at')[:10]

    stats = {
        'total': Consultation.objects.filter(patient=request.user).count(),
        'active': Consultation.objects.filter(patient=request.user, status='active').count(),
        'completed': Consultation.objects.filter(patient=request.user, status='completed').count(),
        'pending': Consultation.objects.filter(patient=request.user, status='pending').count(),
    }
    return render(request, 'dashboard/patient_home.html', {
        'consultations': consultations,
        'stats': stats,
    })


@patient_required
def browse_doctors(request):
    specialty_filter = request.GET.get('specialty', '')
    status_filter = request.GET.get('status', '')

    doctors_qs = DoctorProfile.objects.filter(
        is_verified=True
    ).select_related('user')

    if specialty_filter:
        doctors_qs = doctors_qs.filter(specialty=specialty_filter)
    if status_filter:
        doctors_qs = doctors_qs.filter(availability_status=status_filter)

    doctors_qs = doctors_qs.order_by('-availability_status', '-rating')

    paginator = Paginator(doctors_qs, 12)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'dashboard/browse_doctors.html', {
        'page_obj': page_obj,
        'specialty_choices': DoctorProfile.SPECIALTY_CHOICES,
        'specialty_filter': specialty_filter,
        'status_filter': status_filter,
    })


@patient_required
def new_consultation(request):
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        symptoms = request.POST.get('symptoms_description', '').strip()

        if not doctor_id or not symptoms:
            messages.error(request, 'Please select a doctor and describe your symptoms.')
            return redirect('dashboard:new_consultation')

        try:
            doctor = User.objects.get(pk=doctor_id, role='doctor', doctorprofile__is_verified=True)
        except User.DoesNotExist:
            messages.error(request, 'Invalid doctor selection.')
            return redirect('dashboard:browse_doctors')

        consultation = Consultation.objects.create(
            patient=request.user,
            doctor=doctor,
            symptoms_description=symptoms,
            status='pending',
        )
        messages.success(request, 'Consultation request submitted! The doctor will accept you shortly.')
        return redirect('dashboard:patient_home')

    # GET: load available doctors
    doctors = DoctorProfile.objects.filter(
        is_verified=True, availability_status='online'
    ).select_related('user').order_by('-rating')
    # Pre-select if doctor_id is in GET params
    preselect_doctor = request.GET.get('doctor')
    return render(request, 'dashboard/new_consultation.html', {
        'doctors': doctors,
        'preselect_doctor': preselect_doctor,
    })


@patient_required
def patient_history(request):
    consultations_qs = Consultation.objects.filter(
        patient=request.user
    ).select_related('doctor', 'doctor__doctorprofile').order_by('-created_at')
    paginator = Paginator(consultations_qs, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'consultations/history.html', {
        'page_obj': page_obj,
        'view_as': 'patient',
    })


# ─────────────────────── DOCTOR VIEWS ──────────────────────────

@doctor_required
def doctor_home(request):
    doctor = request.user
    pending_consultations = Consultation.objects.filter(
        doctor=doctor, status='pending'
    ).select_related('patient', 'patient__patientprofile').order_by('created_at')

    active_consultation = Consultation.objects.filter(
        doctor=doctor, status='active'
    ).select_related('patient').first()

    stats = {
        'queue_count': pending_consultations.count(),
        'completed_today': Consultation.objects.filter(
            doctor=doctor, status='completed',
            ended_at__date=timezone.now().date()
        ).count(),
        'total_completed': Consultation.objects.filter(doctor=doctor, status='completed').count(),
    }

    return render(request, 'dashboard/doctor_home.html', {
        'queue': pending_consultations[:5],
        'active_consultation': active_consultation,
        'stats': stats,
        'doctor_profile': doctor.doctorprofile,
    })


@doctor_required
@require_POST
def doctor_status_toggle(request):
    """AJAX POST — toggle doctor availability status."""
    new_status = request.POST.get('status')
    valid_statuses = ['online', 'offline', 'busy']
    if new_status not in valid_statuses:
        return JsonResponse({'status': 'error', 'message': 'Invalid status.'}, status=400)

    request.user.doctorprofile.availability_status = new_status
    request.user.doctorprofile.save()
    return JsonResponse({'status': 'ok', 'availability': new_status})


@doctor_required
@require_POST
def doctor_accept(request):
    """Accept the next pending consultation from the queue."""
    doctor = request.user
    next_consultation = Consultation.objects.filter(
        doctor=doctor, status='pending'
    ).order_by('created_at').first()

    if not next_consultation:
        messages.info(request, 'No pending consultations in your queue.')
        return redirect('dashboard:doctor_home')

    next_consultation.status = 'active'
    next_consultation.started_at = timezone.now()
    next_consultation.save()

    # Mark doctor as busy
    doctor.doctorprofile.availability_status = 'busy'
    doctor.doctorprofile.save()

    return redirect('consultations:room', pk=next_consultation.pk)


@doctor_required
def doctor_history(request):
    consultations_qs = Consultation.objects.filter(
        doctor=request.user
    ).select_related('patient', 'patient__patientprofile').order_by('-created_at')
    paginator = Paginator(consultations_qs, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'consultations/history.html', {
        'page_obj': page_obj,
        'view_as': 'doctor',
    })


# ─────────────────────── ADMIN VIEWS ──────────────────────────

@admin_required
def admin_home(request):
    stats = {
        'total_patients': User.objects.filter(role='patient').count(),
        'total_doctors': User.objects.filter(role='doctor').count(),
        'pending_doctors': DoctorProfile.objects.filter(is_verified=False).count(),
        'consultations_today': Consultation.objects.filter(
            created_at__date=timezone.now().date()
        ).count(),
        'active_consultations': Consultation.objects.filter(status='active').count(),
        'total_consultations': Consultation.objects.count(),
    }
    recent_consultations = Consultation.objects.select_related(
        'patient', 'doctor'
    ).order_by('-created_at')[:10]

    return render(request, 'dashboard/admin_home.html', {
        'stats': stats,
        'recent_consultations': recent_consultations,
    })


@admin_required
def admin_doctors(request):
    doctors = DoctorProfile.objects.select_related('user').order_by('is_verified', 'user__last_name')
    return render(request, 'dashboard/admin_doctors.html', {'doctors': doctors})


@admin_required
@require_POST
def admin_verify_doctor(request, doctor_id):
    profile = get_object_or_404(DoctorProfile, pk=doctor_id)
    profile.is_verified = True
    profile.save()
    messages.success(request, f'Dr. {profile.user.get_full_name()} has been approved.')
    return redirect('dashboard:admin_doctors')


@admin_required
@require_POST
def admin_reject_doctor(request, doctor_id):
    profile = get_object_or_404(DoctorProfile, pk=doctor_id)
    profile.is_verified = False
    profile.save()
    messages.warning(request, f'Dr. {profile.user.get_full_name()} has been rejected.')
    return redirect('dashboard:admin_doctors')


@admin_required
def admin_users(request):
    users = User.objects.exclude(is_superuser=True).order_by('role', 'last_name')
    paginator = Paginator(users, 30)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'dashboard/admin_users.html', {'page_obj': page_obj})

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator
from .forms import PatientRegistrationForm, DoctorRegistrationForm, PatientProfileForm, DoctorProfileForm
from .models import User


class PatientRegistrationView(View):
    template_name = 'accounts/register_patient.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:home')
        form = PatientRegistrationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name}! Your account has been created.')
            return redirect('dashboard:patient_home')
        return render(request, self.template_name, {'form': form})


class DoctorRegistrationView(View):
    template_name = 'accounts/register_doctor.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:home')
        form = DoctorRegistrationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = DoctorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.info(
                request,
                'Your doctor account has been created. Please wait for admin verification before you can access your dashboard.'
            )
            return redirect('accounts:doctor_pending')
        return render(request, self.template_name, {'form': form})


def doctor_pending_view(request):
    return render(request, 'accounts/doctor_pending.html')


@login_required
def profile_view(request):
    user = request.user
    if user.is_patient():
        profile = user.patientprofile
        form_class = PatientProfileForm
        template = 'accounts/profile_patient.html'
    elif user.is_doctor():
        profile = user.doctorprofile
        form_class = DoctorProfileForm
        template = 'accounts/profile_doctor.html'
    else:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=profile)
        # Handle user-level fields
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone = request.POST.get('phone', user.phone)
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        user.save()
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:profile')
    else:
        form = form_class(instance=profile, initial={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
        })
    return render(request, template, {'form': form, 'profile': profile})

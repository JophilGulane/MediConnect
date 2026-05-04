import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.core.files.base import ContentFile
from django.contrib import messages
from accounts.decorators import doctor_required
from consultations.models import Consultation
from .models import Prescription
from .forms import PrescriptionForm
from .pdf import generate_prescription_pdf


@doctor_required
def create_prescription(request, consultation_pk):
    consultation = get_object_or_404(
        Consultation.objects.select_related('patient', 'doctor'),
        pk=consultation_pk
    )

    if consultation.doctor_id != request.user.pk:
        raise PermissionDenied

    if consultation.status != 'completed':
        messages.error(request, 'A prescription can only be created after the consultation is completed.')
        return redirect('consultations:room', pk=consultation_pk)

    # If prescription already exists, redirect to its detail page
    if hasattr(consultation, 'prescription'):
        return redirect('prescriptions:detail', pk=consultation.prescription.pk)

    if request.method == 'POST':
        form = PrescriptionForm(request.POST)
        medicines_json = request.POST.get('medicines_json', '[]')
        try:
            medicines_list = json.loads(medicines_json)
        except (json.JSONDecodeError, TypeError):
            medicines_list = []

        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.consultation = consultation
            prescription.doctor = request.user
            prescription.patient = consultation.patient
            prescription.medicines = medicines_list
            prescription.save()

            # Generate PDF
            try:
                buffer = generate_prescription_pdf(prescription)
                filename = f'prescription_{prescription.pk}.pdf'
                prescription.pdf_file.save(filename, ContentFile(buffer.read()), save=True)
            except Exception as e:
                messages.warning(request, f'Prescription saved but PDF generation failed: {e}')

            # Mark consultation as having a prescription
            consultation.prescription_ready = True
            consultation.save()

            messages.success(request, 'Prescription created and PDF generated successfully.')
            return redirect('prescriptions:detail', pk=prescription.pk)
    else:
        form = PrescriptionForm()

    return render(request, 'prescriptions/create.html', {
        'form': form,
        'consultation': consultation,
    })


@login_required
def prescription_detail(request, pk):
    prescription = get_object_or_404(
        Prescription.objects.select_related('doctor', 'patient', 'consultation', 'doctor__doctorprofile'),
        pk=pk
    )
    if request.user not in [prescription.patient, prescription.doctor]:
        raise PermissionDenied
    return render(request, 'prescriptions/detail.html', {'prescription': prescription})


@login_required
def download_prescription(request, pk):
    prescription = get_object_or_404(Prescription, pk=pk)
    if request.user not in [prescription.patient, prescription.doctor]:
        raise PermissionDenied
    if not prescription.pdf_file:
        raise Http404('PDF not yet generated.')
    return FileResponse(
        prescription.pdf_file.open('rb'),
        as_attachment=True,
        filename=f'prescription_{prescription.pk}.pdf'
    )

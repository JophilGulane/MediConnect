import json
import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.conf import settings
from .models import Consultation, Message, ConsultationImage
from accounts.models import User


def _check_participant(request, consultation):
    if request.user not in [consultation.patient, consultation.doctor]:
        raise PermissionDenied


@login_required
def consultation_room(request, pk):
    consultation = get_object_or_404(
        Consultation.objects.select_related('patient', 'doctor', 'doctor__doctorprofile', 'patient__patientprofile'),
        pk=pk
    )
    _check_participant(request, consultation)

    messages_qs = consultation.messages.select_related('sender').order_by('sent_at')
    images = consultation.images.select_related('uploaded_by').order_by('uploaded_at')

    context = {
        'consultation': consultation,
        'chat_messages': messages_qs,
        'images': images,
        'is_doctor': request.user.is_doctor(),
        'other_party': consultation.patient if request.user.is_doctor() else consultation.doctor,
    }
    return render(request, 'consultations/room.html', context)


@login_required
def fetch_messages(request, pk):
    """AJAX GET — returns all messages as JSON (polling fallback)."""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        raise PermissionDenied
    consultation = get_object_or_404(Consultation, pk=pk)
    _check_participant(request, consultation)

    since_id = request.GET.get('since_id', 0)
    msgs = consultation.messages.filter(pk__gt=since_id).select_related('sender').order_by('sent_at')

    data = []
    for m in msgs:
        data.append({
            'id': m.pk,
            'sender': m.sender.get_full_name() or m.sender.username,
            'sender_id': m.sender.pk,
            'content': m.content,
            'message_type': m.message_type,
            'sent_at': m.sent_at.strftime('%H:%M'),
            'is_self': m.sender_id == request.user.pk,
        })
    return JsonResponse({'status': 'ok', 'messages': data})


@login_required
@require_POST
def upload_image(request, pk):
    """AJAX POST — upload an image to a consultation."""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'status': 'error', 'message': 'AJAX only'}, status=400)

    consultation = get_object_or_404(Consultation, pk=pk)
    _check_participant(request, consultation)

    if consultation.status != 'active':
        return JsonResponse({'status': 'error', 'message': 'Consultation is not active.'}, status=400)

    image_file = request.FILES.get('image')
    if not image_file:
        return JsonResponse({'status': 'error', 'message': 'No image provided.'}, status=400)

    # Validate file size
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if image_file.size > max_bytes:
        return JsonResponse({
            'status': 'error',
            'message': f'Image must be under {settings.MAX_UPLOAD_SIZE_MB}MB.'
        }, status=400)

    # Validate MIME type using Pillow
    try:
        from PIL import Image as PILImage
        img = PILImage.open(image_file)
        if img.format not in ('JPEG', 'PNG', 'WEBP'):
            return JsonResponse({'status': 'error', 'message': 'Only JPEG, PNG, WEBP allowed.'}, status=400)
        image_file.seek(0)
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'Invalid image file.'}, status=400)

    ci = ConsultationImage.objects.create(
        consultation=consultation,
        uploaded_by=request.user,
        image=image_file
    )
    # Also create a Message record
    msg = Message.objects.create(
        consultation=consultation,
        sender=request.user,
        message_type='image',
        content=ci.image.url
    )

    return JsonResponse({
        'status': 'ok',
        'image_url': ci.image.url,
        'sender': request.user.get_full_name() or request.user.username,
        'sender_id': request.user.pk,
        'sent_at': msg.sent_at.strftime('%H:%M'),
        'message_id': msg.pk,
    })


@login_required
@require_POST
def end_consultation(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    if not request.user.is_doctor() or consultation.doctor_id != request.user.pk:
        raise PermissionDenied
    if consultation.status != 'active':
        return redirect('consultations:room', pk=pk)

    consultation.status = 'completed'
    consultation.ended_at = timezone.now()
    consultation.save()
    return redirect('prescriptions:create', consultation_pk=pk)

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.utils.timezone import now
from django.db.models import Count, Q
from .forms import PatientSignUpForm, DoctorLeaveForm
from .models import Doctor, Patient, Appointment, DoctorLeave
from .utils import send_sms
from .models import Notification

def home(request):
    doctors = Doctor.objects.all()
    return render(request, "home.html", {"doctors": doctors})


def patient_register(request):
    if request.method == "POST":
        form = PatientSignUpForm(request.POST)
        if form.is_valid():
            # Save User
            phone = form.cleaned_data.pop("phone", "")
            user = form.save(commit=True)  # creates User
            # Create Patient profile entry
            Patient.objects.create(user=user, phone=phone)
            login(request, user)  # auto-login
            messages.success(request, "Registration successful. Welcome!")
            return redirect("home")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PatientSignUpForm()
    return render(request, "register.html", {"form": form})


# Use Django's built-in login/logout views
class PatientLoginView(LoginView):
    template_name = "login.html"


class PatientLogoutView(LogoutView):
    # uses LOGOUT_REDIRECT_URL from settings
    pass


@login_required
def my_appointments(request):
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return HttpResponseForbidden("You are not registered as a patient.")

    today = now().date()

    upcoming = (
        Appointment.objects.filter(patient=patient, date__gte=today)
        .exclude(status__in=["Cancelled", "Completed"])
        .order_by("date", "time")
    )

    past = (
        Appointment.objects.filter(patient=patient)
        .filter(Q(date__lt=today) | Q(status__in=["Cancelled", "Completed"]))
        .order_by("-date", "-time")
    )

    return render(
        request,
        "my_appointments.html",
        {"upcoming": upcoming, "past": past},
    )


@login_required
def doctor_dashboard(request):
    if not hasattr(request.user, "doctor"):
        return HttpResponseForbidden("Only doctors can access this page.")

    doctor = request.user.doctor
    appointments = doctor.appointment_set.all()
    return render(request, "doctor_dashboard.html", {"appointments": appointments})


@login_required
def book_appointment(request):
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return HttpResponseForbidden("Only patients can book appointments.")

    if request.method == "POST":
        doctor_id = request.POST.get("doctor")
        date = request.POST.get("date")
        time = request.POST.get("time")

        doctor = Doctor.objects.get(id=doctor_id)
        patient = Patient.objects.get(user=request.user)

        Appointment.objects.create(
            doctor=doctor,
            patient=patient,
            date=date,
            time=time,
        )
        messages.success(request, "Appointment requested successfully.")
        return redirect("my_appointments")

    doctors = Doctor.objects.all()
    return render(request, "book_appointment.html", {"doctors": doctors})


@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == "POST":
        appointment.status = "Cancelled"
        appointment.save()

        patient_number = appointment.patient.phone
        msg = (
            f"Dear {appointment.patient.user.username}, your appointment with "
            f"Dr.{appointment.doctor.user.username} on {appointment.date} at {appointment.time} "
            f"has been cancelled."
        )
        send_sms(patient_number, msg)

        messages.success(request, "Appointment cancelled successfully.")
        return redirect("my_appointments")


@login_required
def appointment_action(request, pk):
    """Doctor confirms/rejects/completes appointments for their own patients."""
    appt = get_object_or_404(Appointment, pk=pk)

    if not hasattr(request.user, "doctor") or appt.doctor.user != request.user:
        return HttpResponseForbidden("Only the assigned doctor can perform this action.")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "confirm":
            appt.status = "Confirmed"
            messages.success(request, "Appointment confirmed.")
        elif action == "reject":
            appt.status = "Cancelled"
            messages.success(request, "Appointment rejected.")
        elif action == "complete":
            appt.status = "Completed"
            messages.success(request, "Appointment marked as completed.")
        else:
            messages.error(request, "Unknown action.")
        appt.save()

    return redirect("doctor_dashboard")


@login_required
def patient_history(request):
    if not hasattr(request.user, "patient"):
        return HttpResponseForbidden("Only patients can view this page.")

    patient = request.user.patient
    today = now().date()

    upcoming = Appointment.objects.filter(patient=patient, date__gte=today).order_by("date", "time")
    past = Appointment.objects.filter(patient=patient, date__lt=today).order_by("-date", "-time")

    return render(request, "patient_history.html", {"upcoming": upcoming, "past": past})


@login_required
def doctor_report(request):
    if not hasattr(request.user, "doctor"):
        return redirect("home")

    doctor = request.user.doctor

    stats = doctor.appointment_set.values("status").annotate(total=Count("status"))

    summary = {"Booked": 0, "Confirmed": 0, "Completed": 0, "Cancelled": 0}
    for item in stats:
        summary[item["status"]] = item["total"]

    return render(request, "doctor_report.html", {"summary": summary})

@login_required
def doctor_apply_leave(request):
    if not hasattr(request.user, "doctor"):
        return HttpResponseForbidden("Only doctors can apply leave.")

    doctor = request.user.doctor

    if request.method == "POST":
        form = DoctorLeaveForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.doctor = doctor
            leave.save()

            # Cancel booked appointments on that date
            appointments = Appointment.objects.filter(
                doctor=doctor, date=leave.date, status="Booked"
            )
            for appt in appointments:
                appt.status = "Cancelled"
                appt.save()

                # Save notification for patient
                Notification.objects.create(
                    user=appt.patient.user,
                    message=(
                        f"Your appointment with Dr.{doctor.user.username} on {appt.date} "
                        f"has been cancelled due to leave."
                    )
                )

            messages.success(request, "Leave applied successfully! Patients have been notified.")
            return redirect("doctor_dashboard")
    else:
        form = DoctorLeaveForm()

    return render(request, "apply_leave.html", {"form": form})
@login_required
def my_notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "notifications.html", {"notifications": notifications})



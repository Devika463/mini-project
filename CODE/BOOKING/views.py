from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.utils.timezone import now
from django.db.models import Count, Q
from .forms import PatientSignUpForm, DoctorLeaveForm, MedicalHistoryForm, RescheduleForm
from .models import Doctor, Patient, Appointment, DoctorLeave, Notification, MedicalHistory
from .utils import send_sms
from django.contrib.admin.views.decorators import staff_member_required
from .forms import DoctorSignUpForm
from django.contrib.auth.forms import UserCreationForm
from .forms import PatientRegisterForm
from .forms import DoctorScheduleForm
from .models import DoctorSchedule

# ====================
# AUTH VIEWS
# ====================

class DoctorLoginView(LoginView):
    template_name = "doctor_login.html"

    def get_success_url(self):
        return "/doctor-dashboard/"   # Redirect to doctor dashboard


class PatientLoginView(LoginView):
    template_name = "login.html"


class PatientLogoutView(LogoutView):
    pass


# ====================
# GENERAL VIEWS
# ====================

def welcome(request):
    return render(request, "welcome.html")


def home(request):
    doctors = Doctor.objects.all()
    return render(request, "home.html", {"doctors": doctors})


def patient_register(request):
    if request.method == "POST":
        form = PatientSignUpForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data.pop("phone", "")
            user = form.save(commit=True)
            Patient.objects.create(user=user, phone=phone)
            login(request, user)
            messages.success(request, "Registration successful. Welcome!")
            return redirect("home")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PatientSignUpForm()
    return render(request, "register.html", {"form": form})


# ====================
# PATIENT VIEWS
# ====================

@login_required
def my_appointments(request):
    """Show patient upcoming and past appointments."""
    if not hasattr(request.user, "patient"):
        return HttpResponseForbidden("You are not registered as a patient.")

    patient = request.user.patient
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

    return render(request, "my_appointments.html", {"upcoming": upcoming, "past": past})


@login_required
def patient_history(request):
    """Appointment history (upcoming & past)."""
    if not hasattr(request.user, "patient"):
        return HttpResponseForbidden("Only patients can view this page.")

    patient = request.user.patient
    today = now().date()

    upcoming = Appointment.objects.filter(patient=patient, date__gte=today).order_by("date", "time")
    past = Appointment.objects.filter(patient=patient, date__lt=today).order_by("-date", "-time")

    return render(request, "patient_history.html", {"upcoming": upcoming, "past": past})


@login_required
def patient_medical_history(request):
    """Patient medical history with doctor notes/diagnosis."""
    if not hasattr(request.user, "patient"):
        return HttpResponseForbidden("Only patients can view their medical history.")

    patient = request.user.patient
    history = MedicalHistory.objects.filter(patient=patient).order_by("-created_at")

    return render(request, "medical_history.html", {"history": history})


@login_required
def my_notifications(request):
    if not hasattr(request.user, "patient"):
        return HttpResponseForbidden("Only patients can view notifications.")

    patient = request.user.patient
    notifications = Notification.objects.filter(patient=patient).order_by("-created_at")
    return render(request, "notifications.html", {"notifications": notifications})


@login_required
def search_doctors(request):
    specialization = request.GET.get("specialization")

    if specialization and specialization != "All":
        doctors = Doctor.objects.filter(specialization=specialization)
    else:
        doctors = Doctor.objects.all()

    specializations = Doctor.objects.values_list("specialization", flat=True).distinct()

    return render(request, "search_doctors.html", {
        "doctors": doctors,
        "specializations": specializations,
        "selected": specialization,
    })


@login_required
def book_appointment(request):
    if not hasattr(request.user, "patient"):
        return HttpResponseForbidden("Only patients can book appointments.")

    if request.method == "POST":
        doctor_id = request.POST.get("doctor")
        date = request.POST.get("date")
        time = request.POST.get("time")

        doctor = Doctor.objects.get(id=doctor_id)
        patient = request.user.patient

        Appointment.objects.create(doctor=doctor, patient=patient, date=date, time=time)
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
def reschedule_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=request.user.patient)

    if request.method == "POST":
        form = RescheduleForm(request.POST)
        if form.is_valid():
            new_date = form.cleaned_data['date']
            new_time = form.cleaned_data['time']

            appointment.date = new_date
            appointment.time = new_time
            appointment.status = "Booked"
            appointment.save()

            messages.success(request, "Your appointment has been rescheduled successfully!")
            return redirect("my_appointments")
    else:
        form = RescheduleForm()

    return render(request, "reschedule_appointment.html", {"form": form, "appointment": appointment})


# ====================
# DOCTOR VIEWS
# ====================

@login_required
def doctor_dashboard(request):
    if not hasattr(request.user, "doctor"):
        return HttpResponseForbidden("Only doctors can access this page.")

    doctor = request.user.doctor
    appointments = doctor.appointment_set.all()
    return render(request, "doctor_dashboard.html", {"appointments": appointments})


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

            appointments = Appointment.objects.filter(doctor=doctor, date=leave.date, status="Booked")
            for appt in appointments:
                appt.status = "Cancelled"
                appt.save()
                Notification.objects.create(
                    patient=appt.patient,
                    message=f"Your appointment with Dr.{doctor.user.username} on {appt.date} has been cancelled due to leave."
                )

            messages.success(request, "Leave applied successfully! Patients have been notified.")
            return redirect("doctor_dashboard")
    else:
        form = DoctorLeaveForm()

    return render(request, "apply_leave.html", {"form": form})


@login_required
def appointment_action(request, pk):
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
def add_medical_history(request, patient_id):
    if not hasattr(request.user, "doctor"):
        return HttpResponseForbidden("Only doctors can add history.")

    patient = get_object_or_404(Patient, id=patient_id)
    if request.method == "POST":
        form = MedicalHistoryForm(request.POST)
        if form.is_valid():
            history = form.save(commit=False)
            history.patient = patient
            history.doctor = request.user.doctor
            history.save()
            return redirect("view_medical_history", patient_id=patient.id)
    else:
        form = MedicalHistoryForm()

    return render(request, "add_medical_history.html", {"form": form, "patient": patient})


@login_required
def view_medical_history(request, patient_id=None):
    """Doctor or patient can view medical history."""
    if hasattr(request.user, "patient"):
        patient = request.user.patient
    else:
        if not patient_id:
            return HttpResponseForbidden("Doctor must specify patient.")
        patient = get_object_or_404(Patient, id=patient_id)

    history = MedicalHistory.objects.filter(patient=patient).order_by("-created_at")
    return render(request, "medical_history.html", {"patient": patient, "history": history})

@staff_member_required
def daily_appointments(request):
    selected_date = request.GET.get("date")

    appointments = []
    if selected_date:
        appointments = Appointment.objects.filter(date=selected_date).order_by("time")

    return render(request, "daily_appointments.html", {
        "appointments": appointments,
        "selected_date": selected_date
    })
@login_required
def doctor_register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        specialization = request.POST.get("specialization")

        if form.is_valid():
            user = form.save()  # this saves User
            # create Doctor entry linked to User
            Doctor.objects.create(user=user, specialization=specialization)
            return redirect("login")  # after registration redirect to login
    else:
        form = UserCreationForm()
    return render(request, "doctor_register.html", {"form": form})
def patient_register(request):
    if request.method == "POST":
        form = PatientRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            phone = form.cleaned_data.get("phone")
            Patient.objects.create(user=user, phone=phone)
            return redirect("home")   # or patient dashboard
    else:
        form = PatientRegisterForm()
    return render(request, "patient_register.html", {"form": form})
@login_required
def doctor_schedule_list(request):
    """List and add doctor's schedules."""
    if not hasattr(request.user, "doctor"):
        return HttpResponseForbidden("Only doctors can manage schedules.")

    doctor_user = request.user.doctor   # because DoctorSchedule expects User
    schedules = DoctorSchedule.objects.filter(doctor=doctor_user)

    if request.method == "POST":
        form = DoctorScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.doctor = doctor_user
            schedule.save()
            messages.success(request, "Schedule added successfully.")
            return redirect("doctor_schedule_list")
    else:
        form = DoctorScheduleForm()

    return render(request, "doctor/schedule_list.html", {
        "form": form,
        "schedules": schedules
    })
@login_required
def doctor_schedule_add(request):
    if not hasattr(request.user, "doctor"):
        return HttpResponseForbidden("Only doctors can add schedules.")

    doctor = request.user.doctor

    if request.method == "POST":
        form = DoctorScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.doctor = doctor
            schedule.save()
            messages.success(request, "Schedule added successfully.")
            return redirect("doctor_schedule_list")
    else:
        form = DoctorScheduleForm()

    return render(request, "doctor/schedule_add.html", {"form": form})

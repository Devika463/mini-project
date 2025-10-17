from django import forms
from .models import Appointment, DoctorLeave, MedicalHistory
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Patient
from .models import DoctorSchedule

# ----------------------------
# Patient Sign Up Form
# ----------------------------
class PatientSignUpForm(UserCreationForm):
    phone = forms.CharField(max_length=15, required=True)

    class Meta:
        model = User
        fields = ["username", "email", "phone", "password1", "password2"]


# ----------------------------
# Doctor Leave Form
# ----------------------------
class DoctorLeaveForm(forms.ModelForm):
    class Meta:
        model = DoctorLeave
        fields = ["date", "reason"]


# ----------------------------
# Reschedule Appointment Form
# ----------------------------
class RescheduleForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["date", "time"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
        }


# ----------------------------
# Medical History Form
# ----------------------------
class MedicalHistoryForm(forms.ModelForm):
    class Meta:
        model = MedicalHistory
        fields = ["notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
        }

class DoctorSignUpForm(UserCreationForm):
    specialization = forms.CharField(max_length=100, required=True)
    phone = forms.CharField(max_length=15, required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
class PatientRegisterForm(UserCreationForm):
    phone = forms.CharField(max_length=15, required=True, help_text="Enter your phone number")

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
class DoctorScheduleForm(forms.ModelForm):
    class Meta:
        model = DoctorSchedule
        fields = ["date", "start_time", "end_time"]


from django.contrib import admin
from django.urls import path, include
from booking import views

urlpatterns = [
    path("", views.welcome, name="welcome"),   # Default welcome page
    path("admin/", admin.site.urls),
    path("", include("booking.urls")),   # Include booking app URLs

    # Medical History
    path("medical-history/", views.view_medical_history, name="medical_history"),
    path("medical-history/<int:patient_id>/", views.view_medical_history, name="view_medical_history"),
    path("medical-history/add/<int:patient_id>/", views.add_medical_history, name="add_medical_history"),

    # Admin daily appointments
    path("daily-appointments/", views.daily_appointments, name="daily_appointments"),

    # Doctor self registration
    path("doctor-register/", views.doctor_register, name="doctor_register"),

    # ✅ Doctor schedule management
    path("doctor/schedules/", views.doctor_schedule_list, name="doctor_schedule_list"),
    path("doctor/schedules/add/", views.doctor_schedule_add, name="doctor_schedule_add"),

]

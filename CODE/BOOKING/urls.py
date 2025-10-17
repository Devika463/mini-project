from django.urls import path
from . import views
from .views import DoctorLoginView, welcome

urlpatterns = [
    # Landing / welcome page (separate from app home)
    path("", welcome, name="welcome"),

    # Patient side
    path("home/", views.home, name="home"),   # app home after login
    path("register/", views.patient_register, name="patient_register"),
    path("login/", views.PatientLoginView.as_view(), name="login"),
    path("logout/", views.PatientLogoutView.as_view(), name="logout"),
    path("my-appointments/", views.my_appointments, name="my_appointments"),
    path("book/", views.book_appointment, name="book_appointment"),
    path("cancel/<int:appointment_id>/", views.cancel_appointment, name="cancel_appointment"),
    path("patient-history/", views.patient_history, name="patient_history"),
    path("patient-register/", views.patient_register, name="patient_register"),
    
    # Doctor side
    path("doctor/login/", DoctorLoginView.as_view(), name="doctor_login"),
    path("doctor-dashboard/", views.doctor_dashboard, name="doctor_dashboard"),
    path("appointment-action/<int:pk>/", views.appointment_action, name="appointment_action"),
    path("doctor-report/", views.doctor_report, name="doctor_report"),
    path("doctor/apply-leave/", views.doctor_apply_leave, name="doctor_apply_leave"),
    path("doctor/schedule/", views.doctor_schedule_list, name="doctor_schedule"),


    # Notifications
    path("notifications/", views.my_notifications, name="my_notifications"),
    path("search-doctors/", views.search_doctors, name="search_doctors"),
    path("appointment/<int:appointment_id>/reschedule/", views.reschedule_appointment, name="reschedule_appointment"),
    path("medical-history/", views.patient_medical_history, name="patient_medical_history"),
    path("patients/<int:patient_id>/history/", views.view_medical_history, name="view_medical_history"),
    path("patients/<int:patient_id>/history/add/", views.add_medical_history, name="add_medical_history"),
    path("daily-appointments/", views.daily_appointments, name="daily_appointments"),

]

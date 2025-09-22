from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.patient_register, name="register"),
    path("login/", views.PatientLoginView.as_view(), name="login"),
    path("logout/", views.PatientLogoutView.as_view(), name="logout"),
    path("my-appointments/", views.my_appointments, name="my_appointments"),
    path("book/", views.book_appointment, name="book_appointment"),
    path("cancel/<int:pk>/", views.cancel_appointment, name="cancel_appointment"),
    path("doctor-dashboard/", views.doctor_dashboard, name="doctor_dashboard"),
    path("appointment-action/<int:pk>/", views.appointment_action, name="appointment_action"),

    # ✅ new pages
    path("patient-history/", views.patient_history, name="patient_history"),
    path("doctor-report/", views.doctor_report, name="doctor_report"),
    path("register/", views.patient_register, name="patient_register"),
    path("doctor/apply-leave/", views.doctor_apply_leave, name="doctor_apply_leave"),
    path("notifications/", views.my_notifications, name="my_notifications"),

]

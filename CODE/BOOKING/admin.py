from django.contrib import admin
from django.urls import path
from django.utils.html import format_html
from django.shortcuts import redirect
from .models import Patient, Doctor, Appointment
from . import views


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("user", "phone")


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("user", "specialization")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("doctor", "patient", "date", "time", "status")


# ========== EXTRA ADMIN SETTINGS ==========

# Change headers
admin.site.site_header = "Doctor Appointment Admin"
admin.site.index_title = "Admin Dashboard"
admin.site.site_title = "Doctor Appointment System"


# Add custom URL (Daily Appointments)
def get_admin_urls(urls):
    def get_urls():
        custom_urls = [
            path("daily-appointments/", admin.site.admin_view(views.daily_appointments), name="daily_appointments"),
        ]
        return custom_urls + urls
    return get_urls

admin.site.get_urls = get_admin_urls(admin.site.get_urls())


# Add a clickable link on Admin homepage
def daily_appointments_link():
    return format_html('<a href="/admin/daily-appointments/">📅 View Daily Appointments</a>')

# Inject link into admin index page
admin.site.index_template = "admin/custom_index.html"

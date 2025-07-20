# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, OTP

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'phone_number', 'society_name', 'flat_no', 'is_email_verified', 'is_active')
    list_filter = ('is_email_verified', 'is_active', 'is_staff')
    search_fields = ('email', 'username', 'society_name')

    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone_number', 'society_name', 'flat_no', 'is_email_verified')
        }),
    )

class OTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp_code', 'purpose', 'is_verified', 'created_at')
    list_filter = ('purpose', 'is_verified', 'created_at')
    search_fields = ('user__email', 'otp_code')
    readonly_fields = ('created_at',)

admin.site.register(User, CustomUserAdmin)
admin.site.register(OTP, OTPAdmin)

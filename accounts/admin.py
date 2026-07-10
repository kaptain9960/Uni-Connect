from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
<<<<<<< HEAD
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'school', 'department', 'reputation']
    list_filter = ['role', 'school', 'department', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    autocomplete_fields = ['school', 'department']
    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('role', 'school', 'department', 'matric_number', 'bio', 'avatar', 'reputation')}),
=======
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'department', 'reputation']
    list_filter = ['role', 'department', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('role', 'department', 'matric_number', 'bio', 'avatar', 'reputation')}),
>>>>>>> 6f8229a2a3ef6aa253951614120b14cd7e43809b
    )

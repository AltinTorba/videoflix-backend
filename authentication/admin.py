from django.contrib import admin

from .models import User


@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    """Admin view for the email-based custom user model."""

    list_display = ["id", "email", "is_active", "is_staff"]
    search_fields = ["email"]

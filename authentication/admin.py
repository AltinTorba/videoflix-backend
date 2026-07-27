from django.contrib import admin

from .models import User


@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ["id", "email", "is_active", "is_staff"]
    search_fields = ["email"]

"""
Admin configurations for the clave_unica_auth application.

This module registers the Login and Person models with the Django admin interface
and customizes their appearance and behavior.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Login, Person

# Unregister the default User admin if we are providing a custom one.
# This is conditional on whether a custom UserAdmin is indeed registered below.
# admin.site.unregister(User) # This line is active if the custom UserAdmin below is also active.

class PersonInline(admin.StackedInline):
    """
    Inline admin descriptor for Person model.
    
    Allows editing Person details directly within the User admin page.
    """
    model = Person
    can_delete = False
    # verbose_name_plural = 'Person' # Django defaults to model_name + 's' if not set on model
    # Consider setting verbose_name on the Person model itself for consistency.
    # For an inline representing a single related object, verbose_name_plural might be less intuitive.
    # Using model's verbose_name or setting a specific verbose_name for the inline might be clearer.
    # e.g. verbose_name = 'ClaveÚnica Profile Information'


# It's common to unregister the base User admin only if you're replacing it.
# If UserAdmin is not registered with @admin.register(User), this unregister call might be problematic
# or unnecessary if the goal is just to add an inline to the existing User admin.
# However, the @admin.register(User) decorator implies we are replacing/customizing it.
admin.site.unregister(User) 

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom UserAdmin to include Person information inline.
    """
    inlines = (PersonInline,)

@admin.register(Login)
class LoginAdmin(admin.ModelAdmin):
    """
    Admin view for the Login model.
    
    Displays login attempts and their details. Marked as read-only.
    """
    list_display = ('login_date', 'remote_addr', 'user', 'completed')
    list_filter = ('login_date', 'completed')
    search_fields = ['state', 'remote_addr', 'user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ('state', 'authorization_code', 'login_date', 'remote_addr', 'access_token', 'completed', 'user')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

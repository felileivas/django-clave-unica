"""
Database models for the clave_unica_auth application.

Includes models for:
- Login: Records each ClaveÚnica login attempt and its details.
- Person: Stores ClaveÚnica specific user details linked to a Django User.
"""
from django.db import models
from django.contrib.auth.models import User
import uuid

class Login(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    state = models.UUIDField(default=uuid.uuid4)
    login_date = models.DateTimeField(auto_now=False, auto_now_add=True)
    authorization_code = models.CharField(max_length=120)
    access_token = models.CharField(max_length=120)
    remote_addr = models.CharField(max_length=254, null=True)
    completed = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural ='Login'

    def __str__(self):
        return f"{self.state} | {self.login_date} | {self.user if self.user else ''}"

class Person(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    run_type = models.CharField(max_length=50, blank=True, null=True) # Allow blank/null if data might be missing
    run_num = models.IntegerField(blank=True, null=True) # Allow blank/null
    run_dv = models.CharField(max_length=1, blank=True, null=True) # Allow blank/null
    
    def __str__(self):
        if self.run_num and self.run_dv:
            return f"{self.run_num}-{self.run_dv}"
        return f"Person data for {self.user.username}"
    
    def parse_json(self, info_user_json):
        """Populates the Person instance from ClaveUnica JSON data."""
        rol_unico = info_user_json.get('RolUnico')
        if rol_unico:
            self.run_type = rol_unico.get('tipo')
            self.run_dv = rol_unico.get('DV')
            try:
                self.run_num = int(rol_unico.get('numero'))
            except (ValueError, TypeError):
                # Or log this, or raise a custom error if RUN number is absolutely mandatory for Person
                self.run_num = None 
        # else: handle missing RolUnico if necessary, e.g. log a warning

    @classmethod
    def create_user_from_claveunica_data(cls, info_user_json):
        """Creates a new User instance from ClaveUnica JSON data."""
        rol_unico = info_user_json.get('RolUnico')
        name_data = info_user_json.get('name')

        if not rol_unico:
            raise ValueError("'RolUnico' data missing from ClaveUnica response.")
        if not name_data:
            raise ValueError("'name' data missing from ClaveUnica response.")

        run = rol_unico.get('numero')
        dv = rol_unico.get('DV')
        
        if not run or not dv:
            raise ValueError("RUN or DV missing from ClaveUnica 'RolUnico' data.")

        run_with_dv = f"{run}-{dv}"
        
        email = info_user_json.get('email', '') or ''

        nombres = name_data.get('nombres', [])
        apellidos = name_data.get('apellidos', [])

        first_name = ' '.join(nombres) if nombres else ''
        last_name = ' '.join(apellidos) if apellidos else ''
        
        user = User()
        user.username = run_with_dv
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        return user
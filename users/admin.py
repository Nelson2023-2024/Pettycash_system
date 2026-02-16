from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from  users.models import User,Role

# Register your models here.

admin.site.register(Role)

class CustomUserAdmin(UserAdmin):
    model = User
    ordering = ['email']

    # columns for showing various user fields just like a table on admin
    list_display = ['first_name','last_name','phone_number','email','is_staff', 'last_login','status', 'role',]

    fieldsets = [
        ['Auth Fields', {'fields': ['email', 'password']}],
        ['Personal info', {'fields': ['first_name','last_name','other_name','national_id','phone_number','avatar_url']}],
        ['System Information', {'fields':['status','role','is_active','is_staff','is_superuser','groups','user_permissions']}]
    ]

    search_fields = ['email','first_name','last_name','phone_number']

    add_fieldsets = [
        [None,{'fields':['email','password1','password2','first_name','last_name','role','status','is_staff','is_active']}]
    ]

admin.site.register(User, CustomUserAdmin)
from django.contrib import admin
from .models import User, LoginOTP, CreatePasswordRequest

# Register your models here.
admin.site.register(User)
admin.site.register(CreatePasswordRequest)
admin.site.register(LoginOTP)


#
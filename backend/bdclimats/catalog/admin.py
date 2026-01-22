from django.contrib import admin
from .models import Indicator, ComputationRule

# Register your models here.
admin.site.register(Indicator)
admin.site.register(ComputationRule)
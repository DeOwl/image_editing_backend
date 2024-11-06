from django.contrib import admin
from .models import CustomUser, Filter, Queue, QueueFilter

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Filter)
admin.site.register(Queue)
admin.site.register(QueueFilter)
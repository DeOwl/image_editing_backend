from django.contrib import admin
from .models import Queue, Filter, QueueFilter, CustomUser

admin.site.register(CustomUser)
admin.site.register(Queue)
admin.site.register(Filter)
admin.site.register(QueueFilter)
# Register your models here.

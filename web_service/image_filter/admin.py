from django.contrib import admin
from image_filter.models import CustomUser, Queue, Filter, QueueFilter
# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Queue)
admin.site.register(Filter)
admin.site.register(QueueFilter)
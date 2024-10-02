from image_filter.models import AuthUser, Queue, Filter, QueueFilter
from rest_framework import serializers


class FilterSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = Filter
        # Поля, которые мы сериализуем
        exclude = ["matrix_values", "status", 'id']

class QueueSerializer(serializers.ModelSerializer):
    filters = FilterSerializer(many=True)   
    class Meta:
        # Модель, которую мы сериализуем
        model = Queue
        # Поля, которые мы сериализуем
        exclude = ['status']


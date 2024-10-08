from image_filter.models import AuthUser, Queue, Filter, QueueFilter
from rest_framework import serializers


class FilterSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = Filter
        # Поля, которые мы сериализуем
        fields = ['id','title', 'matrix_values' , 'description', 'status', 'image']
        read_only_fields = ['id']






class QueueFilterSerializer(serializers.ModelSerializer):
    filter = FilterSerializer()
    class Meta:
        # Модель, которую мы сериализуем
        model = QueueFilter
        # Поля, которые мы сериализуем
        fields = ['filter', 'order']

class QueueSerializer(serializers.ModelSerializer):
    filters = QueueFilterSerializer(source="queues", many=True)   
    class Meta:
        # Модель, которую мы сериализуем
        model = Queue
        # Поля, которые мы сериализуем
        fields = ['id', 'status', 'image', 'filters']


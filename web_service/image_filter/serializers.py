from image_filter.models import CustomUser, Queue, Filter, QueueFilter
from rest_framework import serializers



class AllFiltersSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = Filter
        # Поля, которые мы сериализуем
        fields = ['id','title' , 'description', 'image']
        read_only_fields = ['id']


class OneFilterSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = Filter
        # Поля, которые мы сериализуем
        fields = ['id','title', 'matrix_values' , 'description', 'image']
        read_only_fields = ['id']


class QueueSerializer(serializers.ModelSerializer):
    creator = serializers.SlugRelatedField(read_only=True, slug_field="email")
    moderator = serializers.SlugRelatedField(read_only=True, slug_field="email")
    class Meta:
        model = Queue
        fields = ['id', 'creator', 'moderator', 'image_in', 'status', 'creation_date', 'submition_date', 'completion_date']
        read_only_fields = ['id', 'creator', 'image_in', 'creation_date']


class FilterListSerializer(serializers.ModelSerializer):
      filter = AllFiltersSerializer()
      class Meta:
            model = QueueFilter
            fields = ["filter", 'order'] 


class QueueWithFilterSerializer(serializers.ModelSerializer):
        filter_list = serializers.SerializerMethodField()
        
        def get_filter_list(self, obj):
            return FilterListSerializer(obj.queues, many=True).data
        
        image_in = serializers.ReadOnlyField()
        temp_image_in = serializers.ReadOnlyField()
        temp_image_out = serializers.ReadOnlyField()
        creator = serializers.SlugRelatedField(read_only=True, slug_field="email")
        moderator = serializers.SlugRelatedField(read_only=True, slug_field="email")
  

        class Meta:
            model = Queue
            fields = ['id', "creation_date",  "submition_date" , 'creator', 'moderator', 'image_in' , 'temp_image_in', 'temp_image_out', 'filter_list', "status"]
            read_only_fields = ["filter_list"]
            
class ResolveQueue(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=(("finished", "finished"), ("rejected", "rejected")))
    class Meta:
        model = Queue
        fields = ['status']
        


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email', 'password']

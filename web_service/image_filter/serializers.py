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
        fields = ['id','title', 'matrix_values' , 'description', 'image', 'status']
        read_only_fields = ['id']

class QueueSerializer(serializers.ModelSerializer):
    creator = serializers.SlugRelatedField(read_only=True, slug_field="email")
    moderator = serializers.SlugRelatedField(read_only=True, slug_field="email")
    class Meta:
        model = Queue
        fields = "__all__"
        read_only_fields = ['id', 'creator', 'image_in', 'creation_date']


class FilterListSerializer(serializers.ModelSerializer):
      filter = serializers.SerializerMethodField()
      def get_filter(self, obj):
           return {
            'id' : obj.filter.id,
            "title": obj.filter.title,
            "description" : obj.filter.description,
            "image" : obj.filter.image,
        }
      class Meta:
            model = QueueFilter
            fields = ["filter", 'order'] 


class QueueWithFilterSerializer(serializers.ModelSerializer):
        filter_list = serializers.SerializerMethodField()
        temp_image_in = serializers.ReadOnlyField()
        temp_image_out = serializers.ReadOnlyField()
        creator = serializers.SlugRelatedField(read_only=True, slug_field="email")
        moderator = serializers.SlugRelatedField(read_only=True, slug_field="email")

        def get_filter_list(self, obj):
            filter_list = FilterListSerializer(obj.queues, many=True).data
            order_list = [filter['order'] for filter in filter_list]

            filter_list = [filter['filter'] for filter in filter_list]
            for i, filter in enumerate(filter_list):
                 filter['order'] = order_list[i]
  

            return filter_list
        class Meta:
            model = Queue
            fields = ['id', "creation_date",  "submition_date" , 'creator', 'moderator' , 'temp_image_in', 'temp_image_out', 'filter_list', "status"]
            
            
class ResolveQueue(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=(("formed", "formed"), ("finished", "finished")))
    class Meta:
        model = Queue
        fields = ['status']
        


class UserSerializer(serializers.ModelSerializer):
    is_staff = serializers.BooleanField(default=False, required=False)
    is_superuser = serializers.BooleanField(default=False, required=False)
    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'is_staff', 'is_superuser']
        read_only_fields = ['is_staff', 'is_superuser']

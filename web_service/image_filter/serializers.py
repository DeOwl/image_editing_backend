from image_filter.models import AuthUser, Queue, Filter, QueueFilter
from rest_framework import serializers


class FilterSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = Filter
        # Поля, которые мы сериализуем
        fields = ['id','title', 'matrix_values' , 'description', 'status', 'image']
        read_only_fields = ['id']
        
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthUser
        fields = ["username"]

class QueueSerializer(serializers.ModelSerializer):
    creator = serializers.SlugRelatedField(read_only=True, slug_field="username")
    moderator = serializers.SlugRelatedField(read_only=True, slug_field="username")
    class Meta:
        model = Queue
        fields = "__all__"
        read_only_fields = ['id', 'creator', 'image_in', 'creation_date']
        # read_only_fields = ['status']


class FilterListSerializer(serializers.ModelSerializer):
      filter = serializers.SerializerMethodField()
      def get_filter(self, obj):
           return {
            'id' : obj.filter.id,
            "title": obj.filter.title,
            "description" : obj.filter.description,
            "image" : obj.filter.image,
            "matrix_values": obj.filter.matrix_values
        }
      class Meta:
            model = QueueFilter
            fields = ["filter", 'order'] 


class QueueWithFilterSerializer(serializers.ModelSerializer):
        filter_list = serializers.SerializerMethodField()
        temp_image_in = serializers.ReadOnlyField()
        temp_image_out = serializers.ReadOnlyField()

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
    class Meta:
        model = Queue
        fields = ['status']
        


class UserSerializer(serializers.ModelSerializer):
    is_superuser = False
    password = serializers.HiddenField(default="password")
    class Meta:
        model = AuthUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password']
        read_only_fields = ['id']

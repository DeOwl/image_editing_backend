from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, F
from image_filter.serializers import QueueSerializer, FilterSerializer
from image_filter.models import Queue, Filter, AuthUser, QueueFilter
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from minio import Minio
import os
def get_user():
    return AuthUser.objects.get(id=1)

#region Filter

@api_view(['GET'])
def Get_FiltersList(request):
    """
    получение списка фильтров
    """
    # Проверка указали ли фильтр
    title_filter = request.query_params.get("title")
    filters = None
    if title_filter is not None:
        filters = Q(title__icontains=title_filter)
    
    #Получение очереди draft данного пользователя
    req = Queue.objects.filter(creator=get_user().id, status=Queue.QueueStatus.DRAFT).first()

    #получение фильтров
    if filters is not None:
        filter_list = Filter.objects.filter(filters, status=Filter.FilterStatus.GOOD).order_by('id')
    else:
         filter_list = Filter.objects.filter(status=Filter.FilterStatus.GOOD).order_by('id')
    serializer = FilterSerializer(filter_list, many=True)

    cnt = QueueFilter.objects.filter(queue=req.id).count() if req.id is not None else 0
    filter_list = serializer.data
    filter_list.append(f'queue_id : {req.id if req is not None else -1}')
    filter_list.append(f'count: {cnt}')
    
    return Response(
        filter_list,

        status=status.HTTP_200_OK
    )

@api_view(['GET'])
def Get_Filter(request, id):
    """
    получение одного фильтра
    """
    filter = Filter.objects.filter(id=id, status=Filter.FilterStatus.GOOD).first()
    if (filter is None):
        return Response("No such filter", status=status.HTTP_404_NOT_FOUND)
    return Response(FilterSerializer(filter).data, status=status.HTTP_200_OK)

@api_view(['POST'])
def Add_Filter(request):
    """
    добавить новую услугу
    """
    serilizer = FilterSerializer(data=request.data)
    if serilizer.is_valid():
        filter = serilizer.save()
        serilizer = FilterSerializer(filter)
        return Response(serilizer.data, status=status.HTTP_200_OK)
    print(serilizer.errors)
    return Response('Failed to add filter', status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def Change_Filter(request, id):
    """
    изменить услугу
    """
    filter = Filter.objects.filter(id=id).first()
    if filter is None:
        return Response('No such filter', status=status.HTTP_404_NOT_FOUND)
    serializer = FilterSerializer(filter,data=request.data,partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    else:
        return Response('Incorrect data', status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def Delete_Filter(request, id):
    """
    удалить услугу
    """
    filter = Filter.objects.filter(id=id, status=Filter.FilterStatus.GOOD).first()
    if filter is None:
        return Response('No such filter', status=status.HTTP_404_NOT_FOUND)
    if filter.image != '':
        storage = Minio(endpoint=MINIO_ENDPOINT_URL,access_key=MINIO_ACCESS_KEY,secret_key=MINIO_SECRET_KEY,secure=MINIO_SECURE)
        file = filter.image.split("/")[-1]
        try:
            storage.remove_object(MINIO_BUCKET_NAME, file)
        except Exception as exception:
            return Response(f'Failed to remove pic due to {exception}', status=status.HTTP_400_BAD_REQUEST)
        filter.logo_file_path = ""
    filter.status = Filter.FilterStatus.DELETED
    filter.save()
    return Response('Succesfully removed the cargo', status=status.HTTP_200_OK)


#endregion
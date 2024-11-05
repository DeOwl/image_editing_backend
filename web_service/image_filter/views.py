from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q, F
from django.utils.timezone import now
from image_filter.serializers import QueueSerializer, OneFilterSerializer, AllFiltersSerializer, QueueWithFilterSerializer, ResolveQueue, UserSerializer
from image_filter.models import Queue, Filter, QueueFilter, CustomUser

from rest_framework.decorators import api_view
from minio import Minio
from web_service.settings import MINIO_ACCESS_KEY, MINIO_BUCKET_FILTER_NAME, MINIO_ENDPOINT_URL, MINIO_SECURE, MINIO_SECRET_KEY, MINIO_BUCKET_QUEUE_NAME
import cv2
import urllib.request
import numpy as np
from django.core.files.base import ContentFile


from dateutil.parser import parse

import os
def get_user():
    return CustomUser.objects.filter(is_staff=False).first()
def get_moderator():
    return CustomUser.objects.filter(is_staff=True).first()

#region Услуга

@api_view(['GET'])
def Get_Filters_List(request):
    """
    получение списка фильтров
    """
    # Проверка указали ли фильтр
    title_filter = request.query_params.get("title")
    filters = None
    if title_filter is not None:
        filters = Q(title__icontains=title_filter)
    
    #Получение очереди draft данного пользовател
    req = Queue.objects.filter(creator=get_user().id,
                                                status=Queue.QueueStatus.DRAFT).first()
    if req is not None:
        filter_in_queue = QueueFilter.objects.filter(queue=req.id).count() if req.id is not None else 0

    #получение фильтров
    if filters is not None:
        filter_list = Filter.objects.filter(filters, status=Filter.FilterStatus.GOOD).order_by('id')
    else:
         filter_list = Filter.objects.filter(status=Filter.FilterStatus.GOOD).order_by('id')
    serializer = AllFiltersSerializer(filter_list, many=True)
    
    return Response(
        {'filters': serializer.data, 'queue_id' : req.id if req is not None else -1, 'count': filter_in_queue},

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
    return Response(OneFilterSerializer(filter).data, status=status.HTTP_200_OK)

@api_view(['POST'])
def Add_Filter(request):
    """
    добавить новую услугу
    """
    serilizer = OneFilterSerializer(data=request.data)
    if serilizer.is_valid():
        filter = serilizer.save()
        serilizer = OneFilterSerializer(filter)
        return Response(serilizer.data, status=status.HTTP_201_CREATED)
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
    serializer = OneFilterSerializer(filter,data=request.data,partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
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
            storage.remove_object(MINIO_BUCKET_FILTER_NAME, file)
        except Exception as exception:
            return Response(f'Failed to remove pic due to {exception}', status=status.HTTP_400_BAD_REQUEST)
        filter.image = ""
    filter.status = Filter.FilterStatus.DELETED
    filter.save()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
def Add_Filter_Queue(request, id):
    """
    создать новую очередь или добавить к существующей
    """
    filter = Filter.objects.filter(id=id, status=Filter.FilterStatus.GOOD).first()
    if filter is None:
        return Response('No such filter', status=status.HTTP_404_NOT_FOUND)
    
    queue = Queue.objects.filter(creator=get_user(), status = Queue.QueueStatus.DRAFT).first()
    if queue is None:
        queue = Queue(creator=get_user(), status = Queue.QueueStatus.DRAFT, creation_date=now())
        queue.save()

    last_queue_filter = QueueFilter.objects.filter(queue=queue).order_by("order").last()
    if last_queue_filter is None:
        order = 1
    else:
        order = last_queue_filter.order + 1
    filter_queue = QueueFilter(queue=queue, filter=filter, order=order)
    filter_queue.save()
    return Response('Succesfully added filter to queue', status=status.HTTP_201_CREATED)

@api_view(['POST'])
def Load_Filter_Image(request, id):
    """
    загрузить картинку фильтра в минио
    """
    filter = Filter.objects.filter(id=id, status=Filter.FilterStatus.GOOD).first()
    if filter is None:
        return Response('No such filter', status=status.HTTP_404_NOT_FOUND)
    
    if filter.image != '':
        storage = Minio(endpoint=MINIO_ENDPOINT_URL,access_key=MINIO_ACCESS_KEY,secret_key=MINIO_SECRET_KEY,secure=MINIO_SECURE)
        file = filter.image.split("/")[-1]
        try:
            storage.remove_object(MINIO_BUCKET_FILTER_NAME, file)
        except Exception as exception:
            return Response(f'Failed to remove pic due to {exception}', status=status.HTTP_400_BAD_REQUEST)
        filter.image = ""
        filter.save()
    
    storage = Minio(endpoint=MINIO_ENDPOINT_URL,access_key=MINIO_ACCESS_KEY,secret_key=MINIO_SECRET_KEY,secure=MINIO_SECURE)
    file = request.FILES.get("image")
    file_name = f'{id}.{file.name.split(".")[-1]}'
    try:
        storage.put_object(MINIO_BUCKET_FILTER_NAME, file_name, file, file.size)
    except Exception as exception:
        return Response(f'Failed to load pic due to {exception}', status=status.HTTP_400_BAD_REQUEST)
    filter.image = f'http://{MINIO_ENDPOINT_URL}/{MINIO_BUCKET_FILTER_NAME}/{file_name}'
    filter.save()
    return Response('Succesfully added/changed pic', status=status.HTTP_201_CREATED)


#endregion

#region Заявка

@api_view(['GET'])
def Get_Queues_List(request):
    """
    получить список очередей
    """
    status_filter = request.query_params.get("status")
    formation_datetime_start_filter = request.query_params.get("creation_start")
    formation_datetime_end_filter = request.query_params.get("creation_end")
    filter = ~Q(status=Queue.QueueStatus.DELETED)
    filter = ~Q(status=Queue.QueueStatus.DRAFT)
    if status_filter is not None:
        filter &= Q(status=status_filter)
    if formation_datetime_start_filter is not None:
        filter &= Q(creation_date__gte=parse(formation_datetime_start_filter))
    if formation_datetime_end_filter is not None:
        filter &= Q(creation_date__lte=parse(formation_datetime_end_filter))
    queues = Queue.objects.filter(filter)
    serializer = QueueSerializer(queues, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def Get_Queue(request, id):
    """
    получить очередь
    """
    filter = Q(id=id) & ~Q(status=Queue.QueueStatus.DELETED)
    queue = Queue.objects.filter(filter).first()
    if queue is None:
        return Response('No such queue', status=status.HTTP_404_NOT_FOUND)
    serializer = QueueWithFilterSerializer(queue)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST']) #NOTE: Было изменено в соответсвтии с предметной областью
def Change_Queue_Image(request, id):
    """
    изменить изображение очереди
    """
    
    queue = Queue.objects.filter(id=id, status=Queue.QueueStatus.DRAFT).first()
    if queue is None:
        return Response('No such queue', status=status.HTTP_404_NOT_FOUND)
    
    if queue.image_in is not None and queue.image_in != '':
        storage = Minio(endpoint=MINIO_ENDPOINT_URL,access_key=MINIO_ACCESS_KEY,secret_key=MINIO_SECRET_KEY,secure=MINIO_SECURE)
        file ="/".join(queue.image_in.split("/")[-2])
        try:
            storage.remove_object(MINIO_BUCKET_QUEUE_NAME, file)
        except Exception as exception:
            return Response(f'Failed to remove pic due to {exception}', status=status.HTTP_400_BAD_REQUEST)
        queue.image = ""
        queue.save()
    
    storage = Minio(endpoint=MINIO_ENDPOINT_URL,access_key=MINIO_ACCESS_KEY,secret_key=MINIO_SECRET_KEY,secure=MINIO_SECURE)
    file = request.FILES.get("image")
    if file is None:
        return Response(f'No image provided', status=status.HTTP_400_BAD_REQUEST)
    file_name = f'{id}/{file.name}'
    try:
        storage.put_object(MINIO_BUCKET_QUEUE_NAME, file_name, file, file.size)
    except Exception as exception:
        return Response(f'Failed to load pic due to {exception}', status=status.HTTP_400_BAD_REQUEST)
    queue.image_in = f'http://{MINIO_ENDPOINT_URL}/{MINIO_BUCKET_QUEUE_NAME}/{file_name}'
    queue.save()
    return Response('Succesfully added/changed pic', status=status.HTTP_200_OK)


@api_view(['PUT'])
def Form_Queue(request, id):
    """
    сформировать очередь
    """
    queue = Queue.objects.filter(id=id).first()
    if queue is None:
        return Response("This queue does not exist", status=status.HTTP_404_NOT_FOUND)
    if queue.status != Queue.QueueStatus.DRAFT:
        return Response("This queue cannot be formed", status=status.HTTP_400_BAD_REQUEST)

    if queue.image_in is None or queue.image_in == "":
        return Response("No image selected", status=status.HTTP_400_BAD_REQUEST)
    
    queue.status = Queue.QueueStatus.FORMED
    queue.submition_date = now()
    queue.save()
    serializer = QueueSerializer(queue)
    return Response(serializer.data, status=status.HTTP_200_OK)


def Compute_Image(queue):
    req = urllib.request.urlopen(queue.temp_image_in())
    arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
    image = cv2.imdecode(arr, -1)
    for filter_queue in QueueFilter.objects.filter(queue=queue).all():
        arr = list(map(float, filter_queue.filter.matrix_values))
        arr = [[arr[0], arr[1], arr[2]], [arr[3], arr[4], arr[5]], [arr[6], arr[7], arr[8]]]
        kernel = np.array(arr)
        print(kernel)
        image_ = cv2.filter2D(image, -1, kernel)
        image = image_
    ret, buf = cv2.imencode('.png', image) # cropped_image: cv2 / np array
    content = ContentFile(buf.tobytes())
    storage = Minio(endpoint=MINIO_ENDPOINT_URL,access_key=MINIO_ACCESS_KEY,secret_key=MINIO_SECRET_KEY,secure=MINIO_SECURE)
    storage.put_object(MINIO_BUCKET_QUEUE_NAME, f"{queue.id}/out.png", content, content.size)
    return f'http://{MINIO_ENDPOINT_URL}/{MINIO_BUCKET_QUEUE_NAME}/{queue.id}/out.png'
    


@api_view(['PUT'])
def Resolve_Queue(request, id):

    """
    отклонить или завершить оформление
    """
    queue = Queue.objects.filter(id=id).first()
    if queue is None:
        return Response("This queue does not exist", status=status.HTTP_404_NOT_FOUND)
    if queue.status != Queue.QueueStatus.FORMED:
        return Response("This queue cannot be resolved", status=status.HTTP_400_BAD_REQUEST)
    if queue.image_in is None or queue.image_in == "":
        return Response("This queue cannot be resolved", status=status.HTTP_400_BAD_REQUEST)
    serializer = ResolveQueue(queue,data=request.data,partial=True)
    if serializer.is_valid():

        queue = Queue.objects.get(id=id)
        queue.image_out = Compute_Image(queue)
        queue.completion_date = now()
        queue.moderator = get_moderator()
        serializer.save()
        queue.save()
        serializer = QueueSerializer(queue)
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response('Failed to resolve the queue', status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def Delete_Queue(request, id):

    """
    удалить оформление
    """
    queue = Queue.objects.filter(id=id,status=Queue.QueueStatus.DRAFT).first()
    if queue is None:
        return Response("No such Queue", status=status.HTTP_404_NOT_FOUND)

    queue.status = Queue.QueueStatus.DELETED
    queue.save()
    return Response("queue has been succesfully deleted", status=status.HTTP_200_OK)

#endregion

#region M-M

@api_view(['DELETE'])
def Delete_Filter_From_Queue(request, id_queue, order):
    """
    Удаление фильтра из очереди
    """

    
    filter_in_queue = QueueFilter.objects.filter(queue=id_queue, order=order).first()
    if filter_in_queue is None:
        return Response("Queue not found", status=status.HTTP_404_NOT_FOUND)
    if Queue.objects.filter(id=id_queue).first().status != Queue.QueueStatus.DRAFT:
        return Response("NOT ALLOWED", status=status.HTTP_400_BAD_REQUEST)
    filter_in_queue.delete()
    for FilterQueue in QueueFilter.objects.filter(queue=id_queue, order__gt=order).order_by("order"):
        FilterQueue.order -= 1
        FilterQueue.save()
    return Response("deleted", status=status.HTTP_200_OK)


@api_view(['PUT'])
def Switch_Order(request, id_queue, order):
    """
    Изменение данных о грузе в отправлении
    """
    
    filter_1 = QueueFilter.objects.filter(queue=id_queue, order=order).first()
    filter_2 = QueueFilter.objects.filter(queue=id_queue, order=order + 1).first()
    if filter_1 is None:
        return Response("filters in queue not found", status=status.HTTP_404_NOT_FOUND)
    if filter_2 is None:
        return Response("Cannot change order of last filter", status=status.HTTP_400_BAD_REQUEST)
    if Queue.objects.filter(id=id_queue).first().creator != get_user():
        return Response(status=status.HTTP_403_FORBIDDEN)
    if Queue.objects.filter(id=id_queue).first().status != Queue.QueueStatus.DRAFT:
        return Response("NOT ALLOWED", status=status.HTTP_400_BAD_REQUEST)
    if Queue.objects.filter(id=id_queue).first().status != Queue.QueueStatus.DRAFT:
        return Response("NOT ALLOWED", status=status.HTTP_400_BAD_REQUEST)
    filter_1.order = -1
    filter_1.save()
    filter_2.order = order
    filter_2.save()
    filter_1.order = order + 1
    filter_1.save()
    return Response("Succesfull", status=status.HTTP_200_OK)
#endregion



#region User

@api_view(['POST'])
def Create_User(request):
    """
    Создание пользователя
    """
    if CustomUser.objects.filter(email=request.data['email']).exists():
        return Response({'status': 'Exist'}, status=status.HTTP_400_BAD_REQUEST)
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        CustomUser.objects.create_user(email=serializer.data['email'],
                                    password=serializer.data['password'])
        return Response({'status': 'Success'}, status=status.HTTP_200_OK)
    return Response({'status': 'Error', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)




@api_view(['POST'])
def Login_User(request):
    """
    Вход
    """
    return Response('Login', status=status.HTTP_200_OK)
@api_view(['POST'])
def Logout_User(request):

    """
    деавторизация
    """
    return Response('Logout', status=status.HTTP_200_OK)


@api_view(['PUT'])
def Update_User(request, id):
    """
    Обновление данных пользователя
    """
    get_user().set_password(request.query_params.get("password"))
    return Response("OK", status=status.HTTP_200_OK)
#endregion
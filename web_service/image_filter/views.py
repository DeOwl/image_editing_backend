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

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework.decorators import parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.viewsets import ModelViewSet

from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import authentication_classes, permission_classes
from image_filter.permissions import IsAuth, IsAuthManager
from rest_framework.permissions import  AllowAny

from .redis import session_storage
import uuid
from .auth import Auth_by_Session, AuthIfPos

#region Услуга

from rest_framework import serializers

class AllFiltersWithQueue(serializers.Serializer):
    filters = AllFiltersSerializer()
    queue_id = serializers.IntegerField()
    count = serializers.IntegerField()

@swagger_auto_schema(method='get',
                     manual_parameters=[
                         openapi.Parameter('title',
                                           type=openapi.TYPE_STRING,
                                           description='filter title',
                                           in_=openapi.IN_QUERY),
                     ],
                     responses={
                         status.HTTP_200_OK: AllFiltersWithQueue(),
                         status.HTTP_403_FORBIDDEN: "Forbidden",
                     })

@api_view(['GET'])
@permission_classes([AllowAny])
@authentication_classes([AuthIfPos])
def Get_Filters_List(request):
    """
    получение списка фильтров
    """
    # Проверка указали ли фильтр
    title_filter = request.query_params.get("title")
    filters = None
    if title_filter is not None:
        filters = Q(title__icontains=title_filter)
    
    #Получение очереди draft данного пользователя
    user = request.user
    req = None
    filter_in_queue = 0
    if not request.user.is_anonymous:

        req = Queue.objects.filter(creator=user.id,
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

one_filter_good_response = openapi.Response('Получение одного фильтра с матрицей', OneFilterSerializer)
one_filter_bad_response = openapi.Response('Фильтры не получены')

@swagger_auto_schema(method='get', responses={200: one_filter_good_response, 404:one_filter_bad_response})
@api_view(['GET'])
@permission_classes([AllowAny])
def Get_Filter(request, id):
    """ 
    получение одного фильтра
    """
    filter = Filter.objects.filter(id=id, status=Filter.FilterStatus.GOOD).first()
    if (filter is None):
        return Response("No such filter", status=status.HTTP_404_NOT_FOUND)
    return Response(OneFilterSerializer(filter).data, status=status.HTTP_200_OK)

@swagger_auto_schema(method='post', 
                     request_body=OneFilterSerializer, 
                     responses={
                         status.HTTP_200_OK: OneFilterSerializer(),
                         status.HTTP_400_BAD_REQUEST: "Bad Request",
                         status.HTTP_403_FORBIDDEN: "Forbidden",
                     })
@api_view(['POST'])
@permission_classes([IsAuthManager])
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

@swagger_auto_schema(method='put', request_body=OneFilterSerializer,
                      responses={
                         status.HTTP_200_OK: OneFilterSerializer(),
                         status.HTTP_400_BAD_REQUEST: "Bad Request",
                         status.HTTP_404_NOT_FOUND: "Not Found",
                     })
@api_view(['PUT'])
@permission_classes([IsAuthManager])
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


@swagger_auto_schema(method='delete',
                     responses={
                         status.HTTP_200_OK: "OK",
                         status.HTTP_403_FORBIDDEN: "Forbidden",
                         status.HTTP_404_NOT_FOUND: "Not Found",
                     })       
@api_view(['DELETE'])
@permission_classes([IsAuthManager])
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

@swagger_auto_schema(method='post',
                     responses={
                         status.HTTP_200_OK: "OK",
                         status.HTTP_403_FORBIDDEN: "Forbidden",
                         status.HTTP_404_NOT_FOUND: "Not Found",
                     })
@api_view(['POST'])
@permission_classes([IsAuth])
@authentication_classes([Auth_by_Session])
def Add_Filter_Queue(request, id):
    """
    создать новую очередь или добавить к существующей
    """
    filter = Filter.objects.filter(id=id, status=Filter.FilterStatus.GOOD).first()
    if filter is None:
        return Response('No such filter', status=status.HTTP_404_NOT_FOUND)
    
    queue = Queue.objects.filter(creator=request.user, status = Queue.QueueStatus.DRAFT).first()
    if queue is None:
        queue = Queue(creator=request.user, status = Queue.QueueStatus.DRAFT, creation_date=now())
        queue.save()

    last_queue_filter = QueueFilter.objects.filter(queue=queue).order_by("order").last()
    if last_queue_filter is None:
        order = 1
    else:
        order = last_queue_filter.order + 1
    filter_queue = QueueFilter(queue=queue, filter=filter, order=order)
    filter_queue.save()
    return Response('Succesfully added filter to queue', status=status.HTTP_201_CREATED)


@swagger_auto_schema(method='post',
    manual_parameters=[
        openapi.Parameter(name="image",
                          in_=openapi.IN_FORM,
                          type=openapi.TYPE_FILE,
                          required=True)
        ],    
    responses={
        status.HTTP_200_OK: "OK",
        status.HTTP_400_BAD_REQUEST: "Bad Request",
        status.HTTP_403_FORBIDDEN: "Forbidden",
        }              
    )
@api_view(['post'])
@permission_classes([IsAuthManager])
@parser_classes([MultiPartParser])
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
@swagger_auto_schema(method='get',
                     manual_parameters=[
                         openapi.Parameter('status',
                                           type=openapi.TYPE_STRING,
                                           description='status',
                                           in_=openapi.IN_QUERY),
                         openapi.Parameter('formation_start',
                                           type=openapi.TYPE_STRING,
                                           description='status',
                                           in_=openapi.IN_QUERY,
                                           format=openapi.FORMAT_DATETIME),
                         openapi.Parameter('formation_end',
                                           type=openapi.TYPE_STRING,
                                           description='status',
                                           in_=openapi.IN_QUERY,
                                           format=openapi.FORMAT_DATETIME),
                     ],
                     responses={
                         status.HTTP_200_OK: QueueSerializer(many=True),
                         status.HTTP_403_FORBIDDEN: "Forbidden",
                     })
@api_view(['GET'])
@permission_classes([IsAuth])
@authentication_classes([Auth_by_Session])
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
    if not request.user.is_staff:
        filter &= Q(creator=request.user)
    queues = Queue.objects.filter(filter)
    serializer = QueueSerializer(queues, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)





@swagger_auto_schema(method='get',
                     responses={
                         status.HTTP_200_OK: QueueWithFilterSerializer(),
                         status.HTTP_403_FORBIDDEN: "Forbidden",
                         status.HTTP_404_NOT_FOUND: "Not Found",
                     })
@api_view(['GET'])
@permission_classes([IsAuth])
@authentication_classes([Auth_by_Session])
def Get_Queue(request, id):
    """
    получить очередь
    """
    filter = Q(id=id) & ~Q(status=Queue.QueueStatus.DELETED)
    queue = Queue.objects.filter(filter).first()
    if queue is None:
        return Response('No such queue', status=status.HTTP_404_NOT_FOUND)
    if not request.user.is_staff and queue.creator != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)
    serializer = QueueWithFilterSerializer(queue)
    return Response(serializer.data, status=status.HTTP_200_OK)


@swagger_auto_schema(method='POST',
                     manual_parameters=[
                    openapi.Parameter(name="image",
                                    in_=openapi.IN_FORM,
                                    type=openapi.TYPE_FILE,
                                    required=True)
                    ],
                     responses={
                         status.HTTP_200_OK: "OK",
                         status.HTTP_400_BAD_REQUEST: "Bad Request",
                         status.HTTP_403_FORBIDDEN: "Forbidden",
                         status.HTTP_404_NOT_FOUND: "Not Found",
                     })
@api_view(['POST'])
@permission_classes([IsAuth])
@authentication_classes([Auth_by_Session])
@parser_classes([MultiPartParser])
def Change_Queue_Image(request, id):
    """
    изменить изображение очереди
    """
    
    queue = Queue.objects.filter(id=id, status=Queue.QueueStatus.DRAFT).first()
    if queue is None:
        return Response('No such queue', status=status.HTTP_404_NOT_FOUND)
    if queue.creator != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)
    
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

@swagger_auto_schema(method='put',
                     responses={
                         status.HTTP_200_OK: QueueSerializer(),
                         status.HTTP_400_BAD_REQUEST: "Bad Request",
                         status.HTTP_403_FORBIDDEN: "Forbidden",
                         status.HTTP_404_NOT_FOUND: "Not Found",
                     })
@api_view(['PUT'])
@permission_classes([IsAuth])
@authentication_classes([Auth_by_Session])
def Form_Queue(request, id):
    """
    сформировать очередь
    """
    queue = Queue.objects.filter(id=id).first()
    if queue is None:
        return Response("This queue does not exist", status=status.HTTP_404_NOT_FOUND)
    if queue.status != Queue.QueueStatus.DRAFT:
        return Response("This queue cannot be formed", status=status.HTTP_400_BAD_REQUEST)
    if queue.creator != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

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
    


@swagger_auto_schema(method='put', 
                     request_body=ResolveQueue(),
                     responses={
                         status.HTTP_200_OK: QueueSerializer(),
                         status.HTTP_403_FORBIDDEN: "Forbidden",
                         status.HTTP_404_NOT_FOUND: "Not Found",
                         status.HTTP_400_BAD_REQUEST: "bad request"
                     })
@api_view(['PUT'])
@permission_classes([IsAuthManager])
@authentication_classes([Auth_by_Session])
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
        queue.moderator = request.user
        serializer.save()
        queue.save()
        serializer = QueueSerializer(queue)
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response('Failed to resolve the queue', status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='delete',
                     responses={
                         status.HTTP_200_OK: "OK",
                         status.HTTP_403_FORBIDDEN: "Forbidden",
                         status.HTTP_404_NOT_FOUND: "Not Found",
                     })
@api_view(['DELETE'])
@permission_classes([IsAuth])
@authentication_classes([Auth_by_Session])
def Delete_Queue(request, id):

    """
    удалить оформление
    """
    queue = Queue.objects.filter(id=id,status=Queue.QueueStatus.DRAFT).first()
    if queue is None:
        return Response("No such Queue", status=status.HTTP_404_NOT_FOUND)
    
    if queue.creator != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)

    queue.status = Queue.QueueStatus.DELETED
    queue.save()
    return Response("queue has been succesfully deleted", status=status.HTTP_200_OK)

#endregion

#region M-M
@swagger_auto_schema(method='delete',
                     responses={
                         status.HTTP_200_OK: "OK",
                         status.HTTP_403_FORBIDDEN: "Forbidden",
                         status.HTTP_404_NOT_FOUND: "Not Found",
                         status.HTTP_400_BAD_REQUEST: "Bad request"
                     })
@api_view(['DELETE'])
@permission_classes([IsAuth])
@authentication_classes([Auth_by_Session])
def Delete_Filter_From_Queue(request, id_queue, order):
    """
    Удаление фильтра из очереди
    """

    
    filter_in_queue = QueueFilter.objects.filter(queue=id_queue, order=order).first()
    if filter_in_queue is None:
        return Response("Queue not found", status=status.HTTP_404_NOT_FOUND)
    print(Queue.objects.filter(id=id_queue).first().creator.id,  request.user.id)
    if Queue.objects.filter(id=id_queue).first().creator != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)
    if Queue.objects.filter(id=id_queue).first().status != Queue.QueueStatus.DRAFT:
        return Response("NOT ALLOWED", status=status.HTTP_400_BAD_REQUEST)
    filter_in_queue.delete()
    for FilterQueue in QueueFilter.objects.filter(queue=id_queue, order__gt=order).order_by("order"):
        FilterQueue.order -= 1
        FilterQueue.save()
    return Response("deleted", status=status.HTTP_200_OK)


@swagger_auto_schema(method='put',
                     responses={
                         status.HTTP_200_OK: "OK",
                         status.HTTP_400_BAD_REQUEST: "Bad Request",
                         status.HTTP_403_FORBIDDEN: "Forbidden",
                         status.HTTP_404_NOT_FOUND: "Not Found",
                     })
@api_view(['PUT'])
@permission_classes([IsAuth])
@authentication_classes([Auth_by_Session])
def Switch_Order(request, queue, ord):
    """
    Изменение данных о грузе в отправлении
    """
    
    filter_1 = QueueFilter.objects.filter(queue=queue, order=ord).first()
    filter_2 = QueueFilter.objects.filter(queue=queue, order=ord + 1).first()
    if filter_1 is None:
        return Response("filters in queue not found", status=status.HTTP_404_NOT_FOUND)
    if filter_2 is None:
        return Response("Cannot change order of last filter", status=status.HTTP_400_BAD_REQUEST)
    if Queue.objects.filter(id=queue).first().creator != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)
    if Queue.objects.filter(id=queue).first().status != Queue.QueueStatus.DRAFT:
        return Response("NOT ALLOWED", status=status.HTTP_400_BAD_REQUEST)
    if Queue.objects.filter(id=queue).first().status != Queue.QueueStatus.DRAFT:
        return Response("NOT ALLOWED", status=status.HTTP_400_BAD_REQUEST)
    filter_1.order = -1
    filter_1.save()
    filter_2.order = ord
    filter_2.save()
    filter_1.order = ord + 1
    filter_1.save()
    return Response("Succesfull", status=status.HTTP_200_OK)
#endregion



#region User

@swagger_auto_schema(method='post', request_body=UserSerializer)
@api_view(['Post'])
@permission_classes([AllowAny])
def Create_User(request):
    """
    Функция регистрации новых пользователей
    Если пользователя c указанным в request email ещё нет, в БД будет добавлен новый пользователь.
    """
    if CustomUser.objects.filter(email=request.data['email']).exists():
        return Response({'status': 'Exist'}, status=status.HTTP_400_BAD_REQUEST)
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        CustomUser.objects.create_user(email=serializer.data['email'],
                                    password=serializer.data['password'])
        return Response({'status': 'Success'}, status=status.HTTP_200_OK)
    return Response({'status': 'Error', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    


@swagger_auto_schema(method='post',
                     responses={
                         status.HTTP_200_OK: "OK",
                         status.HTTP_400_BAD_REQUEST: "Bad Request",
                     },
                     manual_parameters=[
                         openapi.Parameter('email',
                                           type=openapi.TYPE_STRING,
                                           description='username',
                                           in_=openapi.IN_FORM,
                                           required=True),
                         openapi.Parameter('password',
                                           type=openapi.TYPE_STRING,
                                           description='password',
                                           in_=openapi.IN_FORM,
                                           required=True)
                     ])


@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes((FormParser,))
@csrf_exempt
def Login_User(request):
    email = request.POST.get("email") # допустим передали username и password
    password = request.POST.get("password")
    user = authenticate(email=email, password=password)
    if user is not None:
        session_id = str(uuid.uuid4())
        session_storage.set(session_id, email)
        response = Response(status=status.HTTP_200_OK)
        response.set_cookie("session_id", session_id, samesite="lax")
        return response
    return Response({'error': 'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(method='post',
                     responses={
                         status.HTTP_204_NO_CONTENT: "No content",
                         status.HTTP_403_FORBIDDEN: "Forbidden",
                     })
@api_view(['POST'])
@permission_classes([IsAuth])
def logout_user(request):

    """
    деавторизация
    """
    session_id = request.COOKIES["session_id"]
    print(session_id)
    if session_storage.exists(session_id):
        session_storage.delete(session_id)
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie("session_id")
        return Response(status=status.HTTP_204_NO_CONTENT)

    return Response(status=status.HTTP_403_FORBIDDEN)


@swagger_auto_schema(method='put',
                        manual_parameters=[
                            openapi.Parameter(name="password",
                                            in_=openapi.IN_FORM,
                                            type=openapi.TYPE_STRING,
                                            required=True)
                        ],
                     responses={
                         status.HTTP_200_OK: "OK",
                         status.HTTP_403_FORBIDDEN: "Forbidden",
                     })
@api_view(['PUT'])
@permission_classes([IsAuth])
@authentication_classes([Auth_by_Session])
@parser_classes((FormParser,))
def update_user(request, id):
    """
    Обновление данных пользователя
    """
    # user = request.user
    # serializer = UserSerializer(user, data=request.data, partial=True)
    # if serializer.is_valid():
    #     serializer.save()
    #     return Response(serializer.data, status=status.HTTP_200_OK)
    # return Response('Failed to change user data', status=status.HTTP_400_BAD_REQUEST)
    if request.user.is_staff or request.user.id == id:
        pass
    else:
        return Response(status=status.HTTP_403_FORBIDDEN)
    request.user.set_password(request.query_params.get("password"))
    return Response("OK", status=status.HTTP_200_OK)
#endregion
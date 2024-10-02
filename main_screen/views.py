from django.shortcuts import render, redirect
from django import forms
from datetime import date
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import BadRequest
from django.core.exceptions import PermissionDenied
import requests
from .models import Filter, Queue, QueueFilter, AuthUser
import datetime
from django.db import connection


filters = [
            {'id' : 1, 'image':'http://localhost:9000/filter-images/1.png', 'title': "Gaussian blur",   'description' :'Эффект размытия изображения с помощью размытия по Гауссу 3x3 сверточной матрицей c расширением границ"', 'matrix_values' : [1/16, 1/8, 1/16, 1/8, 1/4, 1/8, 1/16, 1/8, 1/16]},
            {'id' : 2, 'image':'http://localhost:9000/filter-images/2.png', 'title': "Sharpen",         'description' :'Эффект увеличения резкости с помощью сверточной матрицы 3x3', 'matrix_values' : [0, -1, 0, -1, 5, -1, 0, -1, 0]},
            {'id' : 3, 'image':'http://localhost:9000/filter-images/3.png', 'title': "Outline",  'description' :'Эффект выдиления контрастных границ изображения с помощью сверточной матрицы 3x3', 'matrix_values' : [-1, -1, -1, -1, 8, -1, -1, -1, -1]},
            {'id' : 4, 'image':'http://localhost:9000/filter-images/4.png', 'title': "Right Sobel",  'description' :'Эффект выдиления градиента яркости изображения с помощью оператора Собеля', 'matrix_values' : [-1, 0, 1, -2, 0, 2, -1, 0, 1]},]
queues = [{'id' : 0, 'image': 'http://localhost:9000/queue-images/0/foliage_face.jpg', 'filters': [{'id': 0, 'order' : 0}, {'id': 3, 'order' : 1}]},
          {'id' : 1, 'image': 'http://localhost:9000/queue-images/1/foggy_mountains.jpg', 'filters': [{'id': 1, 'order' : 0}, {'id': 2, 'order' : 2}, {'id': 3, 'order' : 1}]}, 
          {'id' : 2, 'image': '', 'filters': [{'id': 1, 'order' : 0}]}, 
          {'id' : 3, 'image': '', 'filters': [{'id': 0, 'order' : 0}]}]

favicon = 'http://localhost:9000/favicon/camera_icon.ico'


current_user = 1
    


@csrf_exempt
def main_page(request):
    try:
        queue_id = Queue.objects.get(creator = current_user, status="draft")
        c = QueueFilter.objects.filter(queue=queue_id).count()
        queue_id = queue_id.id
    except Exception as ex:
        c = -1
        queue_id = -1
        # No queue of type draft

    search = request.GET.get('filter_title', '')
    temp_f = Filter.objects.filter(title__icontains = search, status="good")
    return render(request, 'all_filters.html', { 'data': {
            'filters' : temp_f,
            'queue_count' : c,
            'search' : search,
            'favicon' : favicon,
            'queue_id' : queue_id
        }})


def filter_page(request, id=0):
    try:
        filter_data = Filter.objects.get(id=id)
        return render(request, 'single_filter.html', { 'data': {
            'filter' : filter_data,
            'favicon' : favicon
        }})
    except Exception:
        raise BadRequest('filter not found')

def queue_page(request, id=0):
    try:
        queue = Queue.objects.get(id=id)
    except Exception:
        raise BadRequest('queue not found')
    if (queue.creator.id != current_user):
        raise PermissionDenied()

    filter_data = QueueFilter.objects.select_related("filter").filter(queue=queue).order_by("order")
    
    # check if queue image exists
    try:
        image = Queue.objects.get(id=queue_id).image
        response = requests.get(image)
        if (response.status_code != 200):
            image = ""
    except Exception:
        image = ''

    return render(request, 'queue.html', { 'data': {
        'filters' : filter_data,
        'queue_id' : queue,
        'image' : image.split("/")[-1], 
        'favicon' : favicon
    }})

@csrf_exempt
def add_filter(request, id=0):
    if request.method == "POST":
        filter_id = request.POST.get("filter_id", '')
        try:
            queue = Queue.objects.get(creator = current_user, status="draft")
            count = QueueFilter.objects.filter(queue=queue).count()
        except Exception as ex:
            count = 0
            queue = Queue(status="draft", image='', creation_date = datetime.datetime.now(), creator = AuthUser.objects.get(id=current_user))
            queue.save()
        QueueFilter.objects.create(queue=queue, filter=Filter.objects.get(id=filter_id), order=count + 1)

        return redirect('main_page')
    else:
        raise BadRequest('incorrect method')
    
@csrf_exempt
def remove_queue(request, id=0):
    if request.method == "POST":
        queue_id = request.POST.get("queue_id", '')
        with connection.cursor() as cursor:
            cursor.execute("UPDATE queue SET status = 'deleted' WHERE id = %s", [queue_id])
        return redirect('main_page')
    else:
        raise BadRequest('incorrect method')

from django.shortcuts import render
from django import forms
from datetime import date
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import BadRequest
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import requests




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


queue_id = 1

def count(id):
    return len(list(filter(lambda x: x['id'] == id, queues))[0]['filters'])


@csrf_exempt
def main_page(request):
    print(filters)

    search = request.GET.get('filter_title', '')
    temp_f = list(filter(lambda x: search.lower() in x['title'].lower(), filters))
    return render(request, 'all_filters.html', { 'data': {
            'filters' : temp_f,
            'queue_id' : queue_id,
            'queue_count' : count(queue_id),
            'search' : search,
            'favicon' : favicon
        }})


def filter_page(request, id=0):
    filter_data = list(filter(lambda x: x["id"] == id, filters))
    if len(filter_data) == 1:
        return render(request, 'single_filter.html', { 'data': {
            'filter' : filter_data[0],
            'queue_id' : queue_id,
            'queue_count' : count(queue_id),
            'favicon' : favicon
        }})
    raise BadRequest('filter not found')

def queue_page(request, id=0):
    filter_data = list(filter(lambda x: x['id'] in list(map(lambda x: x["id"], list(filter(lambda x: x["id"] == queue_id, queues))[0]["filters"])), filters))
    for i in filter_data:
        i['order'] = list(filter(lambda x: x['id'] == i['id'], list(filter(lambda x: x["id"] == queue_id, queues))[0]['filters']))[0]['order']
    
    filter_data = sorted(filter_data, key= lambda x:x['order'])


    # check if queue image exists
    image = list(filter( lambda x: x['id'] == id, queues))[0]["image"]
    response = requests.get(image)
    if (response.status_code != 200):
        image = ""

    return render(request, 'queue.html', { 'data': {
        'filters' : filter_data,
        'queue_id' : queue_id,
        'queue_count' : count(queue_id),
        'image' : image.split("/")[-1], 
        'favicon' : favicon
    }})



# Create your views here.

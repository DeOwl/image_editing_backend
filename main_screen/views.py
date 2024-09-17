from django.shortcuts import render
from django import forms
from datetime import date
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import BadRequest
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import requests




filter_path = 'http://localhost:9000/filter-images'
filters = [{'id' : 0,    'title': "RGB Split",       'description' :'Эффект разделения каналов RGB со смещением красного и синего канала в противоположные стороны друг от друга'},
            {'id' : 1,   'title': "Gaussian blur",   'description' :'Эффект размытия изображения с помощью размытия по Гауссу 3x3 сверточной матрицей c расширением границ"'},
            {'id' : 2,   'title': "Sharpen",         'description' :'Эффект увеличения резкости с помощью сверточной матрицы 3x3'},
            {'id' : 3,   'title': "Outline",  'description' :'Эффект выдиления контрастных границ изображения с помощью сверточной матрицы 3x3'},
            {'id' : 4,   'title': "Sobel",  'description' :'Эффект выдиления градиента яркости изображения с помощью оператора Собеля'},
            {'id' : 5,   'title': "Average Grayscale",  'description' :'Эффект черно белого изображения по методу усреднения цветовых каналов изображения'},
            {'id' : 6,   'title': "Luma Grayscale",  'description' :'Эффект черно белого изображения по методу усреднения Luma цветовых каналов с учетом чувствительности глаза к определенным цветовым каналам'}
            ]
queue_path = 'http://localhost:9000/queue-images'
queues = [{'id' : 0, 'image': 'foliage_face.jpg'},
          {'id' : 1, 'image': 'foggy_mountains.jpg'}, 
          {'id' : 2, 'image': ''}, 
          {'id' : 3, 'image': ''}]
queue_filter = [{"queue" : 0, 'filter' : 0}, 
                {"queue" : 0, 'filter' : 3},
                {"queue" : 1, 'filter' : 1},
                {"queue" : 1, 'filter' : 2},
                {"queue" : 1, 'filter' : 3},
                {"queue" : 2, 'filter' : 1},
                {"queue" : 3, 'filter' : 0}]

favicon = 'http://localhost:9000/favicon/camera_icon.ico'


queue_id = 1

def count(id):
    return len(list(filter(lambda x: x['queue'] == id, queue_filter)))


@csrf_exempt
def main_page(request):

    search = request.GET.get('search', '')
    temp_f = list(filter(lambda x: search.lower() in x['title'].lower(), filters))
    for a in temp_f:
        a['image'] = filter_path + '/' + str(a['id']) + ".png"
    return render(request, 'all_filters.html', { 'data': {
            'filters' : temp_f,
            'queue_id' : queue_id,
            'queue_count' : count(queue_id),
            'search' : search,
            'favicon' : favicon
        }})


def filter_page(request, id=0):
    filter_data = list(filter(lambda x: x["id"] == id, filters))
    for a in filter_data:
        a['image'] = filter_path + '/' + str(a['id']) + ".png"
    if len(filter_data) == 1:

        return render(request, 'single_filter.html', { 'data': {
            'filter' : filter_data[0],
            'queue_id' : queue_id,
            'queue_count' : count(queue_id),
            'favicon' : favicon
        }})
    raise BadRequest('filter not found')

def queue_page(request, id=0):
    filter_data = list(filter(lambda x: x['id'] in list(map(lambda x: x['filter'], filter( lambda x: x['queue'] == id, queue_filter))), filters))
    for a in filter_data:
        a['image'] = filter_path + '/' + str(a['id']) + ".png"
    
    image = list(filter( lambda x: x['id'] == id, queues))[0]["image"]
    url = queue_path + "/" + str(id) + "/" + image
    response = requests.get(url)
    if (response.status_code != 200):
        image = ""
    return render(request, 'queue.html', { 'data': {
        'filters' : filter_data,
        'queue_id' : queue_id,
        'queue_count' : count(queue_id),
        'image' : image,
        'favicon' : favicon
    }})



# Create your views here.

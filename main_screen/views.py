from django.shortcuts import render
from django import forms
from datetime import date
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import BadRequest



filters = [{'id' : 0,   'image':"http://localhost:9000/filter-images/rgb-split.jpg",        'title': "RGB Split",       'description' :'Эффект разделения каналов RGB со смещением красного и синего канала в противоположные стороны друг от друга'},
            {'id' : 1,  'image':"http://localhost:9000/filter-images/gaussian_blur.jpg",    'title': "Gaussian blur",   'description' :'test'},
            {'id' : 2,  'image':"http://localhost:9000/filter-images/sharpen.jpg",          'title': "Sharpen",         'description' :'test'},
            {'id' : 3,  'image':"http://localhost:9000/filter-images/outline.png",          'title': "Edge detection",  'description' :'test'}
            ]
queues = [{'id' : 0, 'image': ''},
          {'id' : 1, 'image': ''}, 
          {'id' : 2, 'image': ''}, 
          {'id' : 3, 'image': ''}]
queue_filter = [{"queue" : 0, 'filter' : 0}, 
                {"queue" : 0, 'filter' : 3},
                {"queue" : 1, 'filter' : 1},
                {"queue" : 1, 'filter' : 2},
                {"queue" : 1, 'filter' : 3},
                {"queue" : 2, 'filter' : 1},
                {"queue" : 3, 'filter' : 0}]


queue_id = 1

def count(id):
    return len(list(filter(lambda x: x['queue'] == id, queue_filter)))


@csrf_exempt
def main_page(request):
    print(count(queue_id))

    search = request.GET.get('search', '')
    temp_f = list(filter(lambda x: search in x['title'], filters))
    return render(request, 'all_filters.html', { 'data': {
            'filters' : temp_f,
            'queue_id' : queue_id,
            'cart_count' : count(queue_id)
        }})


def filter_page(request, id=0):
    filter_data = list(filter(lambda x: x["id"] == id, filters))
    if len(filter_data) == 1:
        return render(request, 'single_filter.html', { 'data': {
                'filter' : filter_data[0],
                'queue_id' : queue_id,
                'cart_count' : count(queue_id)
            }})
    raise BadRequest('filter not found')

def queue_page(request, id=0):
    filter_data = list(filter(lambda x: x['id'] in list(map(lambda x: x['filter'], filter( lambda x: x['queue'] == id, queue_filter))), filters))
    return render(request, 'queue.html', { 'data': {
            'filters' : filter_data,
            'queue_id' : queue_id,
            'cart_count' : count(queue_id)
        }})



# Create your views here.

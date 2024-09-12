from django.shortcuts import render
from django import forms
from datetime import date
from django.views.decorators.csrf import csrf_exempt

filters = [{'id' : 0, 'image':"http://localhost:9000/filter-images/rgb-split.jpg", 'title': "RGB Split", 'description' :' test'},
                  {'id' : 1, 'image':"http://localhost:9000/filter-images/gaussian_blur.jpg", 'title': "Gaussian blur", 'description' :'test'},
                  {'id' : 2,'image':"http://localhost:9000/filter-images/sharpen.jpg", 'title': "Sharpen", 'description' :'test'},
                  ]

class searchForm(forms.Form):
    search = forms.CharField(label=False, max_length=100, required=False,widget=forms.TextInput(attrs={'class':"search-bar", 'placeholder':"Поиск"}))


@csrf_exempt
def main_page(request):
    temp_f = filters
    if request.method == "POST":
        form = searchForm(request.POST)
        if form.is_valid():
            s = form.data["search"]
            temp_f = list(filter(lambda x:s.lower() in x['title'].lower(), filters))
    else:
        form = searchForm()
    return render(request, 'all_filters.html', { 'data': {
            'page_name': 'Pictura',
            'filters' : temp_f
        }, 'form' : form})


def filter_page(request, id = 0):
    filter_data = list(filter(lambda x: x["id"] == id, filters))
    if len(filter_data) == 1:
        return render(request, 'single_filter.html', { 'data': {
                'page_name': 'Pictura',
                'filter' : filter_data[0]
            }})
    return




# Create your views here.

"""
URL configuration for web_service project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from image_filter.views import Get_Filters_List, Get_Filter, Add_Filter, Change_Filter, Delete_Filter, Add_Filter_Queue, Load_Filter_Image
from image_filter.views import Get_Queues_List, Get_Queue, Change_Queue_Image, Form_Queue, Resolve_Queue, Delete_Queue
from image_filter.views import Create_User, Login_User, Logout_User, Update_User
from image_filter.views import Delete_Filter_From_Queue, Switch_Order

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('filters', Get_Filters_List),
    path('filters/<int:id>', Get_Filter),
    path('filters/add', Add_Filter),
    path('filters/<int:id>/change', Change_Filter),
    path('filters/<int:id>/delete', Delete_Filter),
    path('filters/<int:id>/add', Add_Filter_Queue),
    path('filters/<int:id>/load', Load_Filter_Image),
    
    path('queue', Get_Queues_List),
    path('queue/<int:id>', Get_Queue),
    path('queue/<int:id>/change', Change_Queue_Image),
    path('queue/<int:id>/form', Form_Queue),
    path('queue/<int:id>/resolve', Resolve_Queue),
    path('queue/<int:id>/delete', Delete_Queue),
    
    path('queue-filters/delete/<int:id_queue>/<int:order>', Delete_Filter_From_Queue),
    path('queue-filters/switch/<int:queue>/<int:ord_1>/<int:ord_2>', Switch_Order),
    
    path('user/create', Create_User), 
    path('user/logout', Logout_User), 
    path('user/login', Login_User), 
    path('user/<int:id>/update', Update_User),
    
]

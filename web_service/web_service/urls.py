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
from image_filter.views import Create_User, Login_User, logout_user, update_user
from image_filter.views import Delete_Filter_From_Queue, Switch_Order
from rest_framework import permissions
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import routers

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    
    path('filters', Get_Filters_List), #список всех фильтров
    path('filters/<int:id>', Get_Filter), #один фильтр
    path('filters/add', Add_Filter), #Добавление фильтра
    path('filters/<int:id>/change', Change_Filter), #Измнение фильтра по id
    path('filters/<int:id>/delete', Delete_Filter),#Удаление фильтра по id
    path('filters/<int:id>/add_to_queue', Add_Filter_Queue), #Удаление фильтра к очереди / создание очереди
    path('filters/<int:id>/load', Load_Filter_Image), #Добавление изображения к фильтру по id
    
    path('queue', Get_Queues_List),
    path('queue/<int:id>', Get_Queue),
    path('queue/<int:id>/change', Change_Queue_Image),
    path('queue/<int:id>/form', Form_Queue),
    path('queue/<int:id>/resolve', Resolve_Queue),
    path('queue/<int:id>/delete', Delete_Queue),
    
    path('queue-filters/delete/<int:id_queue>/<int:order>', Delete_Filter_From_Queue),
    path('queue-filters/switch/<int:queue>/<int:ord>', Switch_Order),
    
    path('user/login',  Login_User, name='login'),
    path('user/logout', logout_user, name='logout'),
    path('user/register', Create_User, name='register'),
    path('user/update', update_user, name='update'),
    
#    path('user/create', Create_User), 
 #   path('user/logout', Logout_User), 
  #  path('user/login', Login_User), 
   # path('user/<int:id>/update', Update_User),
    
]

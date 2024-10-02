from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import status
from image_filter.serializers import QueueSerializer, FilterSerializer
from image_filter.models import Queue, Filter
from rest_framework.views import APIView
from rest_framework.decorators import api_view
import pprint
import json

@api_view(["Get"])
def test(request, format=None):
    q = QueueSerializer(instance = Queue.objects.all(), many="true")
    print(q.data[1])    
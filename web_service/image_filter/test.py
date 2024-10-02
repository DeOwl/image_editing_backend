from serializers import QueueSerializer
from models import Queue

q = QueueSerializer(instance = Queue.objects.all())
print(q.data)
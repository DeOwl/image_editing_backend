from django.db import models
from django.contrib.postgres.fields import ArrayField


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class Filter(models.Model):

    title = models.CharField(max_length=50)
    description = models.TextField()
    image = models.TextField()
    matrix_values = ArrayField(models.FloatField(), size=9)
    status = models.TextField(choices=(("good", "good"), ("deleted", "deleted")))  # This field type is a guess.
    class Meta:
        managed = False
        db_table = 'filter'


class Queue(models.Model):
    class QueueStatus(models.TextChoices):
        DRAFT = "draft"
        DELETED = "deleted"
        FORMED = "formed"
        COMPLETED = "finished"
        REJECTED = "denied"
    status = models.CharField(choices=QueueStatus.choices)
    image_in = models.TextField(blank=True, null=True)
    image_out = models.TextField(blank=True, null=True)
    creation_date = models.DateTimeField()
    submition_date = models.DateTimeField(blank=True, null=True)
    completion_date = models.DateTimeField(blank=True, null=True)
    creator = models.ForeignKey(AuthUser, models.DO_NOTHING, db_column='creator')
    moderator = models.ForeignKey(AuthUser, models.DO_NOTHING, db_column='moderator', related_name='queue_moderator_set', blank=True, null=True)
    
    def temp_image_in(self):
        storage = Minio(endpoint=MINIO_ENDPOINT_URL,access_key=MINIO_ACCESS_KEY,secret_key=MINIO_SECRET_KEY,secure=MINIO_SECURE)
        file = self.image_in
        try:
            url = storage.presigned_get_object(MINIO_BUCKET_QUEUE_NAME, file, timedelta(hours=2))
        except Exception as exception:
            return ""
        return url
        
    def temp_image_out(self):
        storage = Minio(endpoint=MINIO_ENDPOINT_URL,access_key=MINIO_ACCESS_KEY,secret_key=MINIO_SECRET_KEY,secure=MINIO_SECURE)
        file = self.image_out
        try:
            url = storage.presigned_get_object(MINIO_BUCKET_QUEUE_NAME, file, timedelta(hours=2))
        except Exception as exception:
            return ""
        return url

    class Meta:
        managed = False
        db_table = 'queue'


class QueueFilter(models.Model):
    queue = models.ForeignKey(Queue, models.DO_NOTHING, db_column='queue')
    filter = models.ForeignKey(Filter, models.DO_NOTHING, db_column='filter')
    order = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'queue_filter'
        unique_together = (('queue', 'order'),)
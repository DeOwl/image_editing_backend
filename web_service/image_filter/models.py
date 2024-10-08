from django.db import models
from django.contrib.postgres.fields import ArrayField

# Create your models here.

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
    class FilterStatus(models.TextChoices):
        GOOD = "good"
        DELETED = "deleted"

    title = models.CharField(max_length=50)
    description = models.TextField()
    image = models.TextField(default="", blank=True)
    matrix_values = ArrayField(models.FloatField(), size=9)
    status = models.TextField(choices=FilterStatus.choices, default=FilterStatus.GOOD)  # This field type is a guess.
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
    image = models.TextField(blank=True, null=True)
    creation_date = models.DateTimeField()
    submition_date = models.DateTimeField(blank=True, null=True)
    completion_date = models.DateTimeField(blank=True, null=True)
    creator = models.ForeignKey(AuthUser, models.DO_NOTHING, db_column='creator')
    moderator = models.ForeignKey(AuthUser, models.DO_NOTHING, db_column='moderator', related_name='queue_moderator_set', blank=True, null=True)
    filters = models.ManyToManyField(Filter, through="QueueFilter")

    class Meta:
        managed = False
        db_table = 'queue'


class QueueFilter(models.Model):
    queue = models.ForeignKey(Queue, models.DO_NOTHING, db_column='queue', related_name='queues')
    filter = models.ForeignKey(Filter, models.DO_NOTHING, db_column='filter')
    order = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'queue_filter'
        unique_together = (('queue', 'order'),)
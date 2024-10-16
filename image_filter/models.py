from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin

class NewUserManager(BaseUserManager):
    def create_user(self,email,password=None, **extra_fields):
        if not email:
            raise ValueError('User must have an email address')
        
        email = self.normalize_email(email) 
        user = self.model(email=email, **extra_fields) 
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self,email,password=None, **extra_fields):
        user = self.create_user(email, password=password, **extra_fields)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(("email адрес"), unique=True)
    password = models.CharField(max_length=255, verbose_name="Пароль")    
    is_staff = models.BooleanField(default=False, verbose_name="Является ли пользователь менеджером?")
    is_superuser = models.BooleanField(default=False, verbose_name="Является ли пользователь админом?")

    USERNAME_FIELD = 'email'

    objects =  NewUserManager()


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
    status = models.CharField(choices=(("draft", "draft"), ("deleted", "deleted"), ("formed", "formed"), ("finished", "finished"), ("denied", "denied")))
    image_in = models.TextField(blank=True, null=True)
    image_out = models.TextField(blank=True, null=True)
    creation_date = models.DateTimeField()
    submition_date = models.DateTimeField(blank=True, null=True)
    completion_date = models.DateTimeField(blank=True, null=True)
    creator = models.ForeignKey(CustomUser, models.DO_NOTHING, db_column='creator')
    moderator = models.ForeignKey(CustomUser, models.DO_NOTHING, db_column='moderator', related_name='queue_moderator_set', blank=True, null=True)

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
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import User, auth
import uuid
from django.core.validators import RegexValidator
from django.conf import settings
from api.mini_func import *
import os
import json

# Create your models here.

# python manage.py makemigrations
# python manage.py migrate
# python manage.py runserver

# class Tag(mode)


class SystemUser(models.Model):
    uid = models.CharField(unique=True, max_length=255)
    avatar = models.ImageField(
        upload_to="avatars", null=True, blank=True, default='avatars/default-profile.png')
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True, blank=True, null=True)
    gender = models.CharField(max_length=15, null=True, blank=True, choices=[
                              ('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    height = models.FloatField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    is_profile_completed = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.first_name} - {self.uid}"

    def save(self, *args, **kwargs):
        # figure out warranty end date
        if self.height and self.weight and self.gender:
            self.is_profile_completed = True
        super(SystemUser, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class CommonObject(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='images', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class Muscle(CommonObject):
    pass


class Exercise(CommonObject):
    muscle = models.ForeignKey(Muscle, on_delete=models.CASCADE)


class API_Key(models.Model):
    key = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return str(self.key)

    class Meta:
        verbose_name = 'API key'
        verbose_name_plural = 'API keys'

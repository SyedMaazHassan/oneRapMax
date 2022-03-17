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
from random import choice
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
    is_profile_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.first_name} - {self.uid} - {self.is_profile_completed} - ({self.gender}, {self.weight}, {self.height})"

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

    def get_muscle_name(self):
        return self.muscle.name


class Group(models.Model):
    icon = models.CharField(
        default='/media/avatars/default-profile.png', max_length=150)
    name = models.CharField(max_length=50)
    members = models.ManyToManyField("api.SystemUser")
    created_by = models.ForeignKey(
        "api.SystemUser", on_delete=models.CASCADE, related_name="created_by", null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def get_total_members(self):
        return self.members.count()

    def add_admin(self):
        self.members.add(self.created_by)

    def add_single_member(self, user):
        self.members.add(user)

    def add_members(self, member_list):
        for member in member_list:
            member_obj = SystemUser.objects.filter(uid=member).first()
            if member_obj:
                self.add_single_member(member_obj)

    def save(self, *args, **kwargs):
        if not self.pk:
            icon_list = [
                '1.jpg', '2.png', '3.png', '4.jpg', '5.jpg', '7.jpg', '8.jpg', '9.jpg', '10.jpg'
            ]
            self.icon = '/media/groups/' + choice(icon_list)
        super(Group, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Group"
        verbose_name_plural = "Groups"
        ordering = ("-created_at",)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Group_detail", kwargs={"pk": self.pk})


class Entry(models.Model):
    values = models.TextField()
    dates = models.TextField()
    user = models.ForeignKey(SystemUser, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    max_value = models.FloatField(default=0)
    max_value_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f'{self.exercise} - {self.user} - ({self.max_value}, {self.max_value_date})'

    def add_now(self, value, date):
        if self.values and self.dates:
            values = json.loads(self.values)
            dates = json.loads(self.dates)
            if date in dates:
                for i in range(len(dates)):
                    if dates[i] == date and value > values[i]:
                        values[i] = value
            else:
                values.append(value)
                dates.append(date)
            self.set_max_value(values, dates)
            self.values = json.dumps(values)
            self.dates = json.dumps(dates)
        else:
            self.values = json.dumps([value])
            self.dates = json.dumps([date])
            self.max_value = value
            self.max_value_date = date

    def set_max_value(self, values, dates):
        max_val = values[0]
        max_value_index = 0
        for i in range(1, len(values)):
            if values[i] > max_val:
                max_val = values[i]
                max_value_index = i
        self.max_value = max_val
        self.max_value_date = dates[max_value_index]

    class Meta:
        ordering = ("-max_value",)


class API_Key(models.Model):
    key = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return str(self.key)

    class Meta:
        verbose_name = 'API key'
        verbose_name_plural = 'API keys'

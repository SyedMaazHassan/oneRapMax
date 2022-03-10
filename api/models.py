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


class Category(models.Model):
    cat_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=15)
    icon = models.CharField(max_length=15)
    created_at = models.DateTimeField(default=timezone.now)

    def get_next_cat(self):
        all_cats = Category.objects.all()
        length = all_cats.count()
        for index in range(length):
            next_index = index + 1
            if all_cats[index] == self and (next_index < length):
                return all_cats[next_index]
        return None

    def __str__(self):
        return f"{self.name}"

    class Meta:
        ordering = ('cat_id',)


class Course(models.Model):
    course_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=15)
    category = models.ForeignKey(
        Category, related_name='courses', on_delete=models.CASCADE)
    available_on_free_trial = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def get_next_course(self):
        all_courses = Course.objects.filter(category=self.category)
        length = all_courses.count()
        for index in range(length):
            next_index = index + 1
            if all_courses[index] == self and (next_index < length):
                return all_courses[next_index]
        return None

    def __str__(self):
        return f"{self.category} / {self.name} ({self.course_id})"

    class Meta:
        ordering = ('course_id',)


@receiver(post_save, sender=Course)
def unlock_demo_for_all_users(sender, instance, **kwargs):
    if not kwargs['created']:
        all_users = SystemUser.objects.all()
        new_course = instance
        for user in all_users:
            unlock_first_level_and_mission(user, new_course)


class Level(models.Model):
    level_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=15)
    tagline = models.CharField(max_length=70)
    display_pic = models.ImageField(
        upload_to='levels', default='levels/default-display.jpg')
    course = models.ForeignKey(
        Course, related_name='levels', on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    def get_next_level(self):
        all_levels = Level.objects.filter(course=self.course)
        length = all_levels.count()
        for index in range(length):
            next_index = index + 1
            if all_levels[index] == self and (next_index < length):
                return all_levels[next_index]
        return None

    def __str__(self):
        return f"{self.course} / {self.name}"

    class Meta:
        ordering = ('level_id',)


class Mission(models.Model):
    mission_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=15)
    display_pic = models.ImageField(
        upload_to='missions', default='missions/default-display.jpg')
    level = models.ForeignKey(
        Level, related_name='missions', on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    def get_next_mission(self):
        all_missions = Mission.objects.filter(level=self.level)
        length = all_missions.count()
        for index in range(length):
            next_index = index + 1
            if all_missions[index] == self and (next_index < length):
                return all_missions[next_index]
        return None

    def get_length(self, filename):
        data = cv2.VideoCapture(filename)

        # count the number of frames
        frames = data.get(cv2.CAP_PROP_FRAME_COUNT)
        fps = int(data.get(cv2.CAP_PROP_FPS))

        # calculate dusration of the video
        seconds = int(frames / fps)
        video_time = str(timedelta(seconds=seconds))
        return video_time

    def duration(self):
        query = Video.objects.filter(mission=self)
        if query.exists():
            video = query[0]
            video_path = os.path.join(
                settings.BASE_DIR, 'media', str(video.video_url))

            return self.get_length(video_path)
        return None

    def where_you_left_name(self):
        return {
            'mission_id': f'mission/{self.mission_id}',
            'category_name': self.level.course.category.name,
            'mission_name': f'{self.level.course.name} / {self.level.name} / {self.name}'
        }

    def __str__(self):
        return f"{self.level} / {self.name}"

    class Meta:
        ordering = ('mission_id',)


class Video(models.Model):
    video_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=15)
    description = models.CharField(max_length=50)
    mission = models.OneToOneField(
        Mission, related_name='video', on_delete=models.CASCADE)
    video_url = models.FileField(upload_to='videos')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.mission} / {self.title}"

    class Meta:
        ordering = ('video_id',)


class Currency(models.Model):
    code = models.CharField(max_length=6)
    name = models.CharField(max_length=20)
    symbol = models.CharField(max_length=10)

    def __str__(self):
        return f'{self.code}'


class Subscription(models.Model):
    subs_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=30)
    subtitle = models.CharField(max_length=30)
    price = models.FloatField()
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    sales_tax = models.IntegerField(default=9)
    freq = models.CharField(
        max_length=20,
        choices=[('month', 'monthly'), ('year', 'yearly'), ('week', 'weekly')])
    ft_days = models.IntegerField()
    is_best = models.BooleanField(default=False)

    def sales_tax_price(self):
        return round((self.price / 100) * self.sales_tax, 2)

    def total_price(self):
        return round(self.price + self.sales_tax_price(), 2)

    def __str__(self):
        return f'{self.price} {self.currency} / {self.freq} - \
                 (Free trial: {self.ft_days} days)  -  (Best: {self.is_best}) \
                 (Sales tax: {self.sales_tax}%)'

    def save(self, *args, **kwargs):
        if self.is_best:
            Subscription.objects.all().update(is_best=False)
            self.is_best = True
        super(Subscription, self).save(*args, **kwargs)

    class Meta:
        ordering = ('subs_id',)


class Trial(models.Model):
    id = models.AutoField(primary_key=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    started_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    user = models.ForeignKey(
        SystemUser, on_delete=models.CASCADE, null=True, blank=True)

    def end_at(self):
        return self.started_at + timedelta(days=self.subscription.ft_days)

    def update_status(self):
        current_date = timezone.now()
        if current_date >= self.end_at():
            self.is_active = False
            self.save()
            self.user.is_trial_end = True
            self.user.save()
            print("Status updated")

    def __str__(self):
        return f'{self.subscription} by User: {self.user}'


class Payment(models.Model):
    pay_id = models.AutoField(primary_key=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    user = models.ForeignKey(SystemUser, on_delete=models.CASCADE)
    ephemeral_key = models.CharField(max_length=60)
    payment_intent = models.CharField(max_length=60)
    status = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def end_at(self):
        days = 0
        if self.subscription.freq == 'month':
            days = 30
        elif self.subscription.freq == 'year':
            days = 365
        else:
            days = 7
        return self.updated_at + timedelta(days=days)

    def is_expired(self):
        current_date = timezone.now()
        if current_date >= self.end_at():
            return True
        return False

    class Meta:
        ordering = ('pay_id',)


class UnlockedLevel(models.Model):
    level = models.ForeignKey(Level, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    user = models.ForeignKey(
        SystemUser, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f'{self.user} => {self.level} => Completed: {self.is_completed}'


class UnlockedMission(models.Model):
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    user = models.ForeignKey(
        SystemUser, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f'({self.pk}) {self.user} => {self.mission} => Completed: {self.is_completed}'

    class Meta:
        ordering = ('pk',)


class CompletedCourse(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(
        SystemUser, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)


class API_Key(models.Model):
    key = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return str(self.key)

    class Meta:
        verbose_name = 'API key'
        verbose_name_plural = 'API keys'


class LastVisit(models.Model):
    user = models.ForeignKey(SystemUser, on_delete=models.CASCADE)
    mission = models.ForeignKey(
        Mission, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime, timedelta, date
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
import python_avatars as pa

# python manage.py makemigrations
# python manage.py migrate
# python manage.py runserver

# class Tag(mode)


class SystemUser(models.Model):
    uid = models.CharField(unique=True, max_length=255)
    avatar = models.CharField(
        max_length=255, null=True, blank=True, default='avatars/default-profile.png')
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

    def random_string_generator(self, str_size, allowed_chars):
        import random
        return ''.join(random.choice(allowed_chars) for x in range(str_size))

    def add_avatar(self):
        import string
        from django.conf import settings
        chars = "ABCDEFG0123456789HIJKLMNOPQRSTU0123456789VWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        size = 12
        name = self.random_string_generator(size, chars)
        random_avatar = pa.Avatar(
            style=pa.AvatarStyle.CIRCLE,
            hair_color=pa.HairColor.pick_random(),
            # top=pa.HairType.,
            background_color=pa.BackgroundColor.pick_random(),
            eyebrows=pa.EyebrowType.pick_random(),
            mouth=pa.MouthType.SMILE,
            eyes=pa.EyeType.DEFAULT,
            top=pa.HairType.pick_random(),
            nose=pa.NoseType.pick_random(),
            accessory=pa.AccessoryType.NONE,
            clothing=pa.ClothingType.HOODIE,
            clothing_color=pa.ClothingColor.pick_random()
        )
        file_name_temp = name + ".svg"
        file_path = os.path.join(
            settings.BASE_DIR, "media", "avatars", file_name_temp)
        # file_name = "media/" + name + ".svg"
        random_avatar.render(file_path)
        self.avatar = "/media/avatars/" + file_name_temp

    def save(self, *args, **kwargs):
        # figure out warranty end date
        if not self.pk:
            self.add_avatar()

        if self.height and self.weight and self.gender:
            self.is_profile_completed = True

        super(SystemUser, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class Goal(models.Model):
    user = models.ForeignKey(SystemUser, on_delete=models.CASCADE)
    exercise = models.ForeignKey('api.Exercise', on_delete=models.CASCADE)
    weight = models.FloatField()
    is_acheived = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.user.first_name} - {self.reps} -> {self.is_acheived}'

    class Meta:
        ordering = ("-weight",)


class CommonObject(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='images', null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class GoalCounter(models.Model):
    user = models.ForeignKey(SystemUser, on_delete=models.CASCADE)
    records_broke = models.IntegerField(default=0)

    def increment(self):
        self.records_broke += 1
        self.save()

    def reset(self):
        self.records_broke = 0
        self.save()

    def save(self, *args, **kwargs):
        if self.records_broke != 0:
            relavent_badge = Badge.objects.filter(
                requirement=self.records_broke).first()
            if relavent_badge:
                acheivement = Acheivement.objects.filter(
                    user=self.user, badge=relavent_badge).exists()
                if not acheivement:
                    Acheivement.objects.create(
                        user=self.user,
                        badge=relavent_badge
                    )
                    self.reset()

        super(GoalCounter, self).save(*args, **kwargs)

    class Meta:
        ordering = ("-records_broke",)


class Acheivement(models.Model):
    user = models.ForeignKey(SystemUser, on_delete=models.CASCADE)
    badge = models.ForeignKey('api.Badge', on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)


class Badge(CommonObject):
    requirement = models.IntegerField()

    def __str__(self):
        return f'{self.requirement}'

    class Meta:
        ordering = ("requirement",)


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


class SValue(models.Model):
    reps = models.IntegerField()
    dumble_weight = models.FloatField()
    one_rep_value = models.FloatField(null=True, blank=True)
    date = models.DateField(default=date.today)
    entry = models.ForeignKey('Entry', on_delete=models.CASCADE)


class Entry(models.Model):
    user = models.ForeignKey(SystemUser, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    max_value = models.FloatField(default=0)
    max_value_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f'{self.exercise} - {self.user} - ({self.max_value}, {self.max_value_date})'

    def add_now(self, reps, dumble_weight, one_rep_value, date):
        svalues = SValue.objects.filter(entry=self)
        rank_value = round(one_rep_value / self.user.weight, 3)

        if svalues.exists():
            svalue = svalues.filter(date=date).first()

            if svalue:
                print('Already exsits, to replace')
                if one_rep_value > svalue.one_rep_value:
                    svalue.reps = reps
                    svalue.dumble_weight = dumble_weight
                    svalue.one_rep_value = one_rep_value
                    svalue.save()
            else:
                SValue.objects.create(
                    reps=reps,
                    dumble_weight=dumble_weight,
                    one_rep_value=one_rep_value,
                    entry=self,
                    date=date
                )

            if rank_value > self.max_value:
                # updating max value
                self.max_value = rank_value
                self.max_value_date = date

                goal_counter = GoalCounter.objects.filter(
                    user=self.user).first()
                if not goal_counter:
                    raise Exception("Invalid request")
                goal_counter.increment()

        else:
            SValue.objects.create(
                reps=reps,
                dumble_weight=dumble_weight,
                one_rep_value=one_rep_value,
                entry=self,
                date=date
            )
            self.max_value = rank_value
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

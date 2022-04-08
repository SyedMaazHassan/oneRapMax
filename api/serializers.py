from django.db import models
from django.db.models import fields
from rest_framework import serializers
from django.contrib.auth.models import User
from api.models import *

'''
This file contains serializers that is providing
validation and bring data from database safely
under the consideration of checking each parameter
and validate them properly 
'''


class MuscleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Muscle
        exclude = ("created_at",)


class ExerciseToMuscle(serializers.ModelSerializer):
    muscle_name = serializers.CharField(source='get_muscle_name')

    class Meta:
        model = Exercise
        fields = "__all__"


class ExerciseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercise
        exclude = ("created_at", "muscle")


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemUser
        fields = ["uid", "email", "first_name",
                  "last_name", "avatar",  "created_at"]


class GoalSerializer(serializers.ModelSerializer):
    exercise = ExerciseSerializer(many=False, read_only=True)

    class Meta:
        model = Goal
        fields = ['weight', 'exercise', 'is_acheived']


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ["name", "image", "requirement"]


class LeaderBoardSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(many=False, read_only=True)
    is_mine = serializers.SerializerMethodField(method_name='get_is_mine')
    score = serializers.FloatField(source='max_value')
    date = serializers.DateField(source='max_value_date')

    def get_is_mine(self, instance):
        return self.context['user'].uid == instance.user.uid

    class Meta:
        model = Entry
        exclude = ("exercise", "max_value", "max_value_date")


class GroupSerializer(serializers.ModelSerializer):
    total_members = serializers.IntegerField(source='get_total_members')

    class Meta:
        model = Group
        exclude = ("created_by", "members")


class UserSerializer(serializers.ModelSerializer):

    def validate(self, data):
        errors = {}

        if 'phone' in data:
            phone = data['phone']
            phone = phone.replace("-", "")
            if not (phone.isnumeric() and (9 < len(phone) < 15)):
                errors['phone'] = 'Enter a valid phone number'

        if len(errors.keys()) > 0:
            raise serializers.ValidationError(errors)

        return data

    class Meta:
        model = SystemUser
        exclude = ["id"]

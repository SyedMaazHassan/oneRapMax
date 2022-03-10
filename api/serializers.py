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

# Serializer for all the APIs related Script Model (table)


###########################################################
###   FOR Mission Details API         START           #####
###########################################################

class CourseVeryShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['course_id', 'name']


class LevelVeryShortSerializer(serializers.ModelSerializer):
    course = CourseVeryShortSerializer(many=False, read_only=True)

    class Meta:
        model = Level
        fields = ['level_id', 'name', 'course']


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        exclude = ['video_id', 'created_at']


class MissionDetailSerializer(serializers.ModelSerializer):
    level = LevelVeryShortSerializer(many=False, read_only=True)
    video = VideoSerializer(many=False, read_only=True)

    class Meta:
        model = Mission
        fields = '__all__'

###########################################################
###   FOR Mission Details API         END             #####
###########################################################


###########################################################
###   FOR Level Details API           START           #####
###########################################################

class MissionShortSerializer(serializers.ModelSerializer):
    duration = serializers.CharField(max_length=20)

    class Meta:
        model = Mission
        fields = '__all__'


class LevelDetailSerializer(serializers.ModelSerializer):
    missions = MissionShortSerializer(many=True, read_only=True)

    class Meta:
        model = Level
        fields = '__all__'

###########################################################
###   FOR Level Details API           END             #####
###########################################################


###########################################################
###   FOR Category Details API        START           #####
###########################################################

class LevelShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        # fields = '__all__'
        exclude = ['course']


class CourseSerializer(serializers.ModelSerializer):
    levels = LevelShortSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        # fields = '__all__'
        exclude = ["category"]


class CategoryDetailedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


###########################################################
###   FOR Category Details API        END             #####
###########################################################


class CategoryShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


###########################################################
###   FOR Subscription Details API    START           #####
###########################################################


class TrialSerializer(serializers.ModelSerializer):
    end_at = serializers.DateTimeField()

    class Meta:
        model = Trial
        fields = "__all__"


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = "__all__"


class SubscriptionSerializer(serializers.ModelSerializer):
    currency = CurrencySerializer(many=False, read_only=True)
    sales_tax_price = serializers.FloatField()
    total_price = serializers.FloatField()

    class Meta:
        model = Subscription
        fields = "__all__"


###########################################################
###   FOR Subscription Details API    END             #####
###########################################################


class UserSerializer(serializers.ModelSerializer):

    def validate(self, data):
        errors = {}

        if 'phone' in data:
            phone = data['phone']
            if not (phone.isnumeric() and (9 < len(phone) < 15)):
                errors['phone'] = 'Enter a valid phone number'

        if len(errors.keys()) > 0:
            raise serializers.ValidationError(errors)

        return data

    class Meta:
        model = SystemUser
        exclude = ["id"]

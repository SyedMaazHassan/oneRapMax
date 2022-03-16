from django.shortcuts import render
from api.serializers import *
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed
from django.shortcuts import get_object_or_404
# Create your views here.
from api.models import *
from django.conf import settings
from api.authentication import RequestAuthentication, ApiResponse
from api.support import beautify_errors
import copy
import json

# from rest_framework.permissions import IsAuthenticated
# from rest_framework_simplejwt.authentication import JWTAuthentication

# from rest_framework_simplejwt.tokens import RefreshToken
# import jwt


def index(request):
    # all_categories = Category.objects.all()

    # for category in all_categories:
    #     for i in range(3):
    #         new_course = Course(
    #             name = f'Course {i + 1}',
    #             category = category
    #         )
    #         new_course.save()

    #         for j in range(3):
    #             new_level = Level(
    #                 name = f'Level {j + 1}',
    #                 tagline = f"Tagline of level {j + 1}",
    #                 course = new_course
    #             )
    #             new_level.save()

    #             for k in range(3):
    #                 new_mission = Mission(
    #                     name = f'Mission {k + 1}',
    #                     level = new_level
    #                 )
    #                 new_mission.save()

    #     print(category)
    return render(request, "abcc.html")


class SubscriptionApi(APIView, ApiResponse):
    authentication_classes = [RequestAuthentication, ]

    def __init__(self):
        ApiResponse.__init__(self)

    def get_multiple_subscriptions(self):
        all_subs = Subscription.objects.all()
        serializer = SubscriptionSerializer(all_subs, many=True)
        return {'subscriptions': serializer.data}

    def get_trial(self, user_obj, subscription):
        query = Trial.objects.filter(user=user_obj, subscription=subscription)
        result = None
        if query.exists():
            trial = query[0]
            result = TrialSerializer(trial, many=False).data
        return result

    def get_single_subscription(self, subs_id):
        single_sub = get_object_or_404(Subscription, subs_id=subs_id)
        return single_sub

    def get(self, request, subs_id=None):
        try:
            user = SystemUser.objects.get(uid=request.headers['uid'])
            if subs_id:
                single_subscription = self.get_single_subscription(subs_id)
                serialized_data = {}
                print(single_subscription)
                serialized_data['subscription'] = SubscriptionSerializer(
                    single_subscription, many=False).data
                serialized_data['trial'] = self.get_trial(
                    user, single_subscription)
            else:
                serialized_data = self.get_multiple_subscriptions()

            self.postSuccess(
                serialized_data, "Subscriptions fetched successfully")
        except Exception as e:
            self.postError({'subscription': str(e)})
        return Response(self.output_object)

    def post(self, request, subs_id):
        try:
            user = SystemUser.objects.get(uid=request.headers['uid'])

            subscription = Subscription.objects.get(subs_id=subs_id)
            check_query = Trial.objects.filter(
                subscription=subscription,
                user=user
            )
            if check_query.exists():
                self.postError(
                    {'Trial': 'You have already avail the free trial for this subscription'})
                return Response(self.output_object)

            new_trial = Trial(
                subscription=subscription,
                user=user
            )
            new_trial.save()
            user.is_trial_taken = True
            user.save()
            output = {
                "trial": TrialSerializer(new_trial, many=False).data
            }

            self.postSuccess(output, "Free trial has been started!")
        except Exception as e:
            self.postError({'Trial': str(e)})
        return Response(self.output_object)


class LevelApi(APIView, ApiResponse):
    authentication_classes = [RequestAuthentication, ]

    def __init__(self):
        ApiResponse.__init__(self)

    def check_access(self, level, user_obj):
        query = UnlockedLevel.objects.filter(
            user=user_obj,
            level=level
        )
        return query.exists()

    def get(self, request, level_id=None):
        if not level_id:
            self.postError({'level_id': 'Level id is missing'})
            return Response(self.output_object)
        try:
            single_level = Level.objects.get(level_id=level_id)
            serializer = LevelDetailSerializer(single_level, many=False)
            # Get logged in user
            user_obj = SystemUser.objects.get(uid=request.headers['uid'])

            if not self.check_access(single_level, user_obj):
                self.postError({'level': 'This level is locked'})
                return Response(self.output_object)

            # Convert data into python dictionary to process
            proper_data = json.loads(json.dumps(serializer.data))
            # Get all unlocked missions
            unlocked_missions = UnlockedMission.objects.filter(user=user_obj)

            all_missions = proper_data['missions']
            for mission_index in range(len(all_missions)):
                mission = all_missions[mission_index]

                mission['is_locked'] = True
                mission['is_completed'] = False
                query_test = unlocked_missions.filter(
                    mission_id=mission['mission_id'])
                if query_test.exists():
                    mission['is_locked'] = False
                    if query_test[0].is_completed:
                        mission['is_completed'] = True

            self.postSuccess({'level': proper_data},
                             "Level fetched successfully")

        except Exception as e:
            self.postError({'level': str(e)})
        return Response(self.output_object)


class CategoryApi(APIView, ApiResponse):
    authentication_classes = [RequestAuthentication, ]

    def __init__(self):
        ApiResponse.__init__(self)

    def get_multiple_categories(self):
        all_categories = Category.objects.all()
        serializer = CategoryShortSerializer(all_categories, many=True)
        return {'categories': serializer.data}

    def get_courses(self, category, user):
        related_courses = self.get_related_courses(user, category)
        courses = CourseSerializer(related_courses, many=True).data
        courses = json.loads(json.dumps(courses))
        return courses

    def get_completed_courses(self, category, user):
        all_completed_courses = CompletedCourse.objects.filter(
            user=user, course__category=category).values_list('course_id', flat=True)
        return list(all_completed_courses)

    def apply_ticks_on_courses(self, course, completed_courses):
        if course['course_id'] in completed_courses:
            is_completed = True
        else:
            is_completed = False
        course['is_completed'] = is_completed

    def get_unlocked_levels(self, user):
        unlocked_levels = UnlockedLevel.objects.filter(
            user=user).values_list('level_id', 'is_completed')
        return unlocked_levels

    def apply_ticks_on_levels(self, level, unlocked_levels):
        level['is_locked'] = True
        level['is_completed'] = False
        single_unlocked_level = unlocked_levels.filter(
            level_id=level['level_id']).first()
        if single_unlocked_level:
            level['is_locked'] = False
            level['is_completed'] = True if single_unlocked_level[1] else False

    def serialize_where_you_left(self, user, category):
        last_visited_mission = self.add_where_you_left_mission(user, category)
        # data = MissionShortSerializer(last_visited_mission, many = False).data
        return last_visited_mission

    def get_single_category(self, cat_id, user_obj):
        single_cat = get_object_or_404(Category, cat_id=cat_id)
        serializer = CategoryDetailedSerializer(single_cat, many=False)
        proper_data = json.loads(json.dumps(serializer.data))
        all_courses = self.get_courses(single_cat, user_obj)
        all_completed_courses = self.get_completed_courses(
            single_cat, user_obj)
        all_unlocked_levels = self.get_unlocked_levels(user_obj)

        for course in all_courses:
            self.apply_ticks_on_courses(course, all_completed_courses)
            all_levels = course['levels']
            for level in all_levels:
                self.apply_ticks_on_levels(level, all_unlocked_levels)
        proper_data['courses'] = all_courses

        if len(all_courses) > 0:
            if all_courses == all_completed_courses:
                proper_data['where_you_left'] = {
                    'mission_id': None,
                    'category_name': single_cat.name,
                    'mission_name': 'All courses completed!'
                }
            else:
                proper_data['where_you_left'] = self.add_where_you_left_mission(
                    user_obj, single_cat)
        else:
            proper_data['where_you_left'] = {
                'mission_id': None,
                'category_name': single_cat.name,
                'mission_name': 'No courses present!'
            }
        return {'category': proper_data}

    def get(self, request, cat_id=None):
        try:
            user_object = SystemUser.objects.get(uid=request.headers['uid'])
            self.add_payment_info(user_object)
            if cat_id:
                serialized_data = self.get_single_category(cat_id, user_object)
            else:
                serialized_data = self.get_multiple_categories()
            self.postSuccess(
                serialized_data, "Category(s) fetched successfully")
        except Exception as e:
            self.postError({'cat': str(e)})
        return Response(self.output_object)


def get_objs(muscle_id, exercise_id):
    muscle = get_object_or_404(Muscle, id=muscle_id)
    exercise = Exercise.objects.get(id=exercise_id, muscle=muscle)
    return {
        'muscle': muscle,
        'exercise': exercise
    }


class LeaderBoard(APIView, ApiResponse):
    authentication_classes = [RequestAuthentication]

    def __init__(self):
        ApiResponse.__init__(self)

    def get(self, request, muscle_id, exercise_id):
        try:
            output = {}
            user = SystemUser.objects.get(uid=request.headers['uid'])
            objs = get_objs(muscle_id, exercise_id)
            group_id = request.data.get("group_id")
            if not group_id:
                all_entries = Entry.objects.filter(exercise=objs['exercise'])
                serialized_entries = LeaderBoardSerializer(
                    all_entries, many=True, context={'user': user})
                output['leaderboard'] = serialized_entries.data
            self.postSuccess(output, "Exercise fetched successfully")
        except Exception as e:
            self.postError({'exercise': str(e)})
        return Response(self.output_object)


class ExerciseApi(APIView, ApiResponse):
    authentication_classes = [RequestAuthentication]

    def __init__(self):
        ApiResponse.__init__(self)

    def get_serialized_version(self, user, muscle, exercise):
        serialized_muscle = MuscleSerializer(muscle, many=False)
        serialized_exercise = ExerciseSerializer(exercise, many=False)
        entry = Entry.objects.filter(user=user, exercise=exercise).first()
        if entry:
            dates = json.loads(entry.dates)
            values = json.loads(entry.values)
        else:
            dates = values = []

        return {
            'exercise': serialized_exercise.data,
            'muscle': serialized_muscle.data,
            'dates': dates,
            'values': values
        }

    def get_response(self, user, muscle_id, exercise_id):
        output = get_objs(muscle_id, exercise_id)
        output['response_output'] = self.get_serialized_version(
            user, output['muscle'], output['exercise'])
        return output

    def calculate_onerap_max(self, weight, reps):
        oneRapMax = weight * (36 / (37 - reps))
        oneRapMax = "{:.5f}".format(oneRapMax)
        return float(oneRapMax)

    def post(self, request, muscle_id, exercise_id):
        try:
            objs = get_objs(muscle_id, exercise_id)
            reps = request.data.get('reps')
            print(reps)
            if reps and reps.isdigit() and int(reps) > 0 and int(reps) < 37:
                reps = int(reps)
                user = SystemUser.objects.get(uid=request.headers['uid'])
                muscel = objs['muscle']
                exercise = objs['exercise']

                entry = Entry.objects.filter(
                    user=user, exercise=exercise).first()
                date = datetime.now().strftime("%Y-%m-%d")
                one_rap_max = self.calculate_onerap_max(user.weight, reps)
                if not entry:
                    entry = Entry(user=user, exercise=exercise)
                entry.add_now(one_rap_max, date)
                entry.save()
                print(entry.values, entry.dates)
                serialized_version = self.get_serialized_version(
                    user, objs['muscle'], objs['exercise'])
                self.postSuccess(serialized_version,
                                 "New one rap max has been submitted successfully")
            else:
                self.postError({
                    'one rap max': 'Provide valid value of no. of "reps"'
                })
        except Exception as e:
            self.postError({'one rap max': str(e)})
        return Response(self.output_object)

    def get(self, request, muscle_id, exercise_id):
        try:
            user = SystemUser.objects.get(uid=request.headers['uid'])
            output = self.get_response(user, muscle_id, exercise_id)
            self.postSuccess(output['response_output'],
                             "Exercise fetched successfully")
        except Exception as e:
            self.postError({'exercise': str(e)})
        return Response(self.output_object)


class MuscleApi(APIView, ApiResponse):
    authentication_classes = [RequestAuthentication]

    def __init__(self):
        ApiResponse.__init__(self)

    def get_all_muscles(self):
        all_muscles = Muscle.objects.all()
        all_muscles_sd = MuscleSerializer(all_muscles, many=True)
        return all_muscles_sd.data

    def get_exercises_by_muscle(self, muscle):
        all_exercises = muscle.exercise_set.all()
        return ExerciseSerializer(all_exercises, many=True).data

    def get_single_muscle(self, muscle):
        single_muscle_sd = MuscleSerializer(muscle, many=False)
        return single_muscle_sd.data

    def get(self, request, muscle_id=None):
        try:
            output_dict = None
            if muscle_id:
                muscle = get_object_or_404(Muscle, id=muscle_id)
                output_dict = {
                    'muscle': self.get_single_muscle(muscle),
                    'exercises': self.get_exercises_by_muscle(muscle)
                }
            else:
                output_dict = {'muscle': self.get_all_muscles()}
            self.postSuccess(output_dict, "Muscle fetched successfully")
        except Exception as e:
            self.postError({'muscle': str(e)})
        return Response(self.output_object)


class UserApi(APIView, ApiResponse):
    authentication_classes = [RequestAuthentication]

    def __init__(self):
        ApiResponse.__init__(self)

    def post(self, request, uid=None):
        try:
            data = request.data.copy()
            data['uid'] = uid
            serializer = UserSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                user = SystemUser.objects.get(uid=uid)
                self.postSuccess({'user': serializer.data},
                                 "User added successfully")
            else:
                self.postError(beautify_errors(serializer.errors))
        except Exception as e:
            self.postError({'uid': str(e)})
        return Response(self.output_object)

    def get(self, request, uid=None):
        try:
            if not uid:
                raise Exception("UID is missing")
            user = get_object_or_404(SystemUser, uid=uid)
            serializer = UserSerializer(user, many=False)

            self.postSuccess({'user': serializer.data},
                             "User fetched successfully")
        except Exception as e:
            self.postError({'uid': str(e)})
        return Response(self.output_object)

    def patch(self, request, uid=None):
        try:
            user_obj = get_object_or_404(SystemUser, uid=uid)
            if 'email' in request.data and user_obj.email != request.data['email']:
                self.postError(
                    {'email': 'To avoid problems with future signin, Email cannot be updated'})
                return Response(self.output_object)

            serializer = UserSerializer(
                user_obj, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                self.postSuccess({'user': serializer.data},
                                 "User updated successfully")
            else:
                self.postError(beautify_errors(serializer.errors))
        except Exception as e:
            self.postError({'uid': str(e)})
        return Response(self.output_object)

    # def post(self, request, uid):

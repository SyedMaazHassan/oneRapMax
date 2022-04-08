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
from django.db.models import Q
from django.db.models import Value
from django.db.models.functions import Concat
from random import choice
import re
# from rest_framework.permissions import IsAuthenticated
# from rest_framework_simplejwt.authentication import JWTAuthentication

# from rest_framework_simplejwt.tokens import RefreshToken
# import jwt


def index(request):

    # Completely random avatar

    # Completely random avatar except for the hat
    # More attributes can stay fixed

    # for user in SystemUser.objects.all():
    #     GoalCounter.objects.create(user=user)
    #     user.save()

    # import requests

    # users = SystemUser.objects.all()
    # all_exercises = Exercise.objects.all()
    # numbers = list(range(12, 36))
    # weights = list(range(15, 45))
    # url = 'http://127.0.0.1:8000/'
    # for user in users[:10]:
    #     headers = {
    #         'api-key': '0a0302b5-c298-42f1-b030-db9e08034ae2',
    #         'uid': user.uid,
    #         "Content-Type": "application/json; charset=utf-8"
    #     }
    #     print("---------------------")
    #     print("USER STARTED", user)
    #     print("---------------------")
    #     for exercise in all_exercises:
    #         url = f'http://127.0.0.1:8000/api/muscles/{exercise.muscle.id}/exercise/{exercise.id}'

    #         print(f"========= EXERCISE STARTED - {exercise} ========")
    #         for i in range(15, 25):
    #             reps = choice(numbers)
    #             weight = choice(weights)
    #             date = f'2022-03-{i}'

    #             data = {
    #                 'reps': reps,
    #                 'weight': weight,
    #                 'date': date
    #             }

    #             r = requests.post(url, headers=headers, json=data)
    #             print(r.json())

    #         print("========= EXERCISE STARTED ========")
    #     print("---------------------")
    #     print("USER ENDED", user)
    #     print("---------------------")

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
    context = {
        'badges': Badge.objects.all()
    }
    date = datetime.now().strftime("%Y-%m-%d")
    query = SValue.objects.filter(date=date)
    print(query)
    return render(request, "abcc.html", context)


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

    def get(self, request):
        try:
            output = {}
            exercise_id = request.query_params.get("exercise_id")
            group_id = request.query_params.get("group_id")
            user = SystemUser.objects.get(uid=request.headers['uid'])
            if not exercise_id:
                raise Exception("Please select the exercise")
            exercise = Exercise.objects.get(id=exercise_id)
            all_entries = Entry.objects.filter(exercise=exercise)

            if group_id:
                group = Group.objects.filter(
                    created_by=user, id=group_id).first()
                if group:
                    all_entries = all_entries.filter(
                        user__in=group.members.all())
                else:
                    raise Exception(
                        "Group doesn't exist or you don't have access fetch this data")
            print(all_entries)
            serialized_entries = LeaderBoardSerializer(
                all_entries, many=True, context={'user': user})
            output['leaderboard'] = serialized_entries.data
            self.postSuccess(output, "Leaderboard data fetched successfully")
        except Exception as e:
            self.postError({'error': str(e)})
        return Response(self.output_object)


class GroupApi(APIView, ApiResponse):
    authentication_classes = [RequestAuthentication]

    def __init__(self):
        ApiResponse.__init__(self)

    def get(self, request):
        try:
            user = SystemUser.objects.get(uid=request.headers['uid'])
            groups = Group.objects.filter(created_by=user)
            groups_serialized = GroupSerializer(groups, many=True)
            self.postSuccess({'groups': groups_serialized.data},
                             'Groups fetched created successfully')
        except Exception as e:
            self.postError({'Group': str(e)})
        return Response(self.output_object)

    def is_group_exists(self, user, name):
        all_groups = Group.objects.filter(created_by=user, name__exact=name)
        return all_groups.exists()

    def delete(self, request, id):
        try:
            user = SystemUser.objects.get(uid=request.headers['uid'])
            group = Group.objects.filter(created_by=user, id=id).first()
            if not group:
                raise Exception(
                    "Group doesn't exist or you don't have access to delete it")
            group.delete()
            self.postSuccess({}, 'Group has been deleted successfully')
        except Exception as e:
            self.postError({'Group': str(e)})
        return Response(self.output_object)

    def post(self, request):
        try:
            name = request.data.get('name')
            members = request.data.get('members')
            user = SystemUser.objects.get(uid=request.headers['uid'])
            if name and members:
                if not self.is_group_exists(user, name):
                    new_group = Group(name=name, created_by=user)
                    new_group.save()
                    new_group.add_members(members)
                    new_group.add_admin()
                    group_serialized = GroupSerializer(new_group)
                    output = {
                        'group': group_serialized.data
                    }
                    self.postSuccess(
                        output, 'Group has been created successfully')
                else:
                    self.postError(
                        {'Group': 'Group with this name already exists'})
            else:
                self.postError(
                    {'Group': 'Please add valid info. to create group'})
        except Exception as e:
            self.postError({'Group': str(e)})
        return Response(self.output_object)


class AllExerciseApi(APIView, ApiResponse):
    authentication_classes = [RequestAuthentication]

    def __init__(self):
        ApiResponse.__init__(self)

    def get(self, request):
        try:
            user = SystemUser.objects.get(uid=request.headers['uid'])
            all_exercises = Exercise.objects.all()
            all_exercises_serialized = ExerciseToMuscle(
                all_exercises, many=True)
            self.postSuccess({'exercises': all_exercises_serialized.data},
                             'Exercises fetched created successfully')
        except Exception as e:
            self.postError({'Exercises': str(e)})
        return Response(self.output_object)


class ExerciseApi(APIView, ApiResponse):
    authentication_classes = [RequestAuthentication]

    def __init__(self):
        ApiResponse.__init__(self)

    def get_serialized_version(self, user, muscle, exercise):
        serialized_muscle = MuscleSerializer(muscle, many=False)
        serialized_exercise = ExerciseSerializer(exercise, many=False)
        entry = Entry.objects.filter(user=user, exercise=exercise).first()
        max_value = None
        if entry:
            max_value = entry.max_value
            svalues = SValue.objects.filter(entry=entry)
            dates = list(svalues.values_list('date', flat=True))
            values = list(svalues.values_list('one_rep_value', flat=True))
        else:
            dates = values = []

        return {
            'exercise': serialized_exercise.data,
            'muscle': serialized_muscle.data,
            'dates': dates,
            'values': values,
            'max_reps_value': max_value,
        }

    def get_response(self, user, muscle_id, exercise_id):
        output = get_objs(muscle_id, exercise_id)
        output['response_output'] = self.get_serialized_version(
            user, output['muscle'], output['exercise'])
        return output

    def get_reps(self, onerapmax_value):
        reps = 37 - (36 / onerapmax_value)
        return int(reps)

    def calculate_onerap_max(self, weight, reps):
        oneRapMax = weight * (36 / (37 - reps))
        # oneRapMax = "{:.5f}".format(oneRapMax)
        return round(oneRapMax, 3)
        # return float(oneRapMax)

    def post(self, request, muscle_id, exercise_id):
        try:
            objs = get_objs(muscle_id, exercise_id)
            reps = request.data.get('reps')
            goal = request.data.get('goal')
            weight = request.data.get('weight')
            date = request.data.get('date')
            user = SystemUser.objects.get(uid=request.headers['uid'])
            exercise = objs['exercise']
            print(goal)
            output = {}

            if reps and weight:
                if str(reps).isdigit() and int(reps) > 0 and int(reps) < 37 and str(weight).isdigit() and int(weight) > 0:
                    reps = int(reps)
                    weight = int(weight)
                    muscel = objs['muscle']

                    # Update goal status
                    all_goals_acheived = Goal.objects.filter(
                        user=user, weight__lte=weight, is_acheived=False)
                    all_goals_acheived.update(is_acheived=True)
                    print(all_goals_acheived)

                    entry = Entry.objects.filter(
                        user=user, exercise=exercise).first()
                    # date = datetime.now().strftime("%Y-%m-%d")

                    print(reps)
                    one_rap_max = self.calculate_onerap_max(weight, reps)
                    print(one_rap_max)
                    if not entry:
                        entry = Entry(user=user, exercise=exercise)
                        entry.save()
                    entry.add_now(reps, weight, one_rap_max, date)
                    entry.save()

                    serialized_version = self.get_serialized_version(
                        user, objs['muscle'], objs['exercise'])
                    output = serialized_version
                else:
                    raise Exception(
                        "Invalid value for 'reps'. Value should be 0 > number < 37")

            if goal:
                if str(goal).isdigit() and int(goal) > 0:
                    new_goal = Goal(user=user, exercise=exercise, weight=goal)
                    new_goal.save()
                    print(output)
                    output['goal'] = 'Goal has been added'
                else:
                    raise Exception(
                        "Invalid value for 'goal'. Value should be 0 > number < 37")

            if (not (goal or reps)):
                self.postError({
                    'exercise_form': "'Invalid value for 'reps' or 'goal'"
                })
            else:
                self.postSuccess(output, "Data has been saved successfully")

        except Exception as e:
            self.postError({'exercise_form': str(e)})
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


class GoalApi(APIView, ApiResponse):
    authentication_classes = [RequestAuthentication]

    def __init__(self):
        ApiResponse.__init__(self)

    def get(self, request):
        try:
            user = SystemUser.objects.get(uid=request.headers['uid'])
            all_goals = Goal.objects.filter(user=user)
            serialized_all_goals = GoalSerializer(all_goals, many=True).data
            self.postSuccess({
                'goals': serialized_all_goals
            }, 'Goals have been fetched')
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


class AllUserApi(APIView, ApiResponse):
    authentication_classes = [RequestAuthentication]

    def __init__(self):
        ApiResponse.__init__(self)

    def get(self, request, uid=None):
        try:
            all_users = SystemUser.objects.exclude(uid=request.headers['uid'])
            all_users_serialized = UserMiniSerializer(all_users, many=True)
            self.postSuccess({'users': all_users_serialized.data},
                             "Users fetched successfully")
        except Exception as e:
            self.postError({'Users': str(e)})
        return Response(self.output_object)


class UserSearchApi(APIView, ApiResponse):
    authentication_classes = [RequestAuthentication]

    def __init__(self):
        ApiResponse.__init__(self)

    def get(self, request):
        try:
            uid = request.headers['uid']
            user = SystemUser.objects.get(uid=uid)

            query = request.query_params.get("query")
            users = []
            if query:
                query = re.sub(' +', ' ', query)
                all_users = SystemUser.objects.all().exclude(uid=uid)
                all_users = all_users.annotate(full_name=Concat(
                    'first_name', Value(' '), 'last_name'))
                searched_users = all_users.filter(
                    Q(full_name__icontains=query) | Q(email__icontains=query))
                serialized_searched_users = UserMiniSerializer(
                    searched_users, many=True).data
                users = serialized_searched_users
            output = {'users': users}
            self.postSuccess(
                output, "Search result users fetched successfully")
        except Exception as e:
            self.postError({'search_users': str(e)})
        return Response(self.output_object)


class AchievementApi(APIView, ApiResponse):
    authentication_classes = [RequestAuthentication]

    def __init__(self):
        ApiResponse.__init__(self)

    def get(self, request):
        try:
            user = SystemUser.objects.get(uid=request.headers['uid'])
            all_achivements = Acheivement.objects.filter(
                user=user).values_list("badge_id", flat=True)

            got = Badge.objects.filter(Q(id__in=all_achivements))
            to_get = Badge.objects.filter(~Q(id__in=all_achivements))

            serialized_got = BadgeSerializer(got, many=True).data
            serialized_to_get = BadgeSerializer(to_get, many=True).data

            output = {
                'got': serialized_got,
                'to_get': serialized_to_get
            }
            self.postSuccess(output, "Badges fetched successfully")
        except Exception as e:
            self.postError({'badge': str(e)})
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
                GoalCounter.objects.create(user=user)
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

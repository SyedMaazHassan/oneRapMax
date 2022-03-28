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
    # user.save()

    # users = SystemUser.objects.all()
    # all_exercises = Exercise.objects.all()
    # numbers = list(range(105, 201))
    # for user in users[:10]:
    #     print("---------------------")
    #     print("USER STARTED", user)
    #     print("---------------------")
    #     for exercise in all_exercises:
    #         print(f"========= EXERCISE STARTED - {exercise} ========")
    #         values = [106 / user.weight]
    #         dates = ['2022-03-15']
    #         max_value = 106 / user.weight
    #         max_value_date = '2022-03-15'
    #         for i in range(16, 25):
    #             val = choice(numbers)
    #             val = val / user.weight
    #             date = f'2022-03-{i}'
    #             if val > max(values):
    #                 max_value = val
    #                 max_value_date = date
    #             values.append(val)
    #             dates.append(date)
    #         new_entry = Entry(
    #             values=json.dumps(values),
    #             dates=json.dumps(dates),
    #             user=user,
    #             exercise=exercise,
    #             max_value=max_value,
    #             max_value_date=max_value_date
    #         )
    #         new_entry.save()
    #         print(values, dates)
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
    return render(request, "abcc.html", context)


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
            dates = json.loads(entry.dates)
            values = json.loads(entry.values)
            max_value = self.get_reps(entry.max_value)
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
        oneRapMax = (36 / (37 - reps))
        oneRapMax = "{:.5f}".format(oneRapMax)
        return float(oneRapMax)

    def post(self, request, muscle_id, exercise_id):
        try:
            objs = get_objs(muscle_id, exercise_id)
            reps = request.data.get('reps')
            goal = request.data.get('goal')
            user = SystemUser.objects.get(uid=request.headers['uid'])
            exercise = objs['exercise']
            print(goal)
            output = {}

            if reps:
                if str(reps).isdigit() and int(reps) > 0 and int(reps) < 37:
                    reps = int(reps)
                    muscel = objs['muscle']
                    print(reps)

                    # Update goal status
                    all_goals_acheived = Goal.objects.filter(
                        user=user, reps__lte=reps, is_acheived=False)
                    all_goals_acheived.update(is_acheived=True)
                    print(all_goals_acheived)

                    entry = Entry.objects.filter(
                        user=user, exercise=exercise).first()
                    date = datetime.now().strftime("%Y-%m-%d")
                    print(reps)
                    one_rap_max = self.calculate_onerap_max(user.weight, reps)
                    print(one_rap_max)
                    if not entry:
                        entry = Entry(user=user, exercise=exercise)
                    entry.add_now(one_rap_max, date)
                    entry.save()
                    print(entry.values, entry.dates)
                    serialized_version = self.get_serialized_version(
                        user, objs['muscle'], objs['exercise'])
                    output = serialized_version
                else:
                    raise Exception(
                        "Invalid value for 'reps'. Value should be 0 > number < 37")

            if goal:
                if str(goal).isdigit() and int(goal) > 0 and int(goal) < 37:
                    new_goal = Goal(user=user, exercise=exercise, reps=goal)
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

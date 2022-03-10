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
import stripe
stripe.api_key = settings.STRIPE['secretKey']

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


class PaymentApi(APIView, ApiResponse):
    authentication_classes = [RequestAuthentication, ]

    def __init__(self):
        ApiResponse.__init__(self)

    def create_ephemeral_key(self, stripe_cust_id):
        ephemeralKey = stripe.EphemeralKey.create(
            customer=stripe_cust_id,
            stripe_version="2020-03-02"
        )
        return ephemeralKey.secret

    def create_payment_intent(self, stripe_cust_id, subs_object):
        paymentIntent = stripe.PaymentIntent.create(
            amount=int(subs_object.total_price() * 100),
            currency=subs_object.currency.code,
            customer=stripe_cust_id,
            automatic_payment_methods={
                'enabled': True,
            }
        )
        return paymentIntent.client_secret

    def post(self, request):
        try:
            user = SystemUser.objects.get(uid=request.headers['uid'])
            payment_intent = request.data['paymentIntent']
            ephemeral_key = request.data['ephemeralKey']
            status = request.data['status']
            if int(status) not in [1, -1]:
                raise Exception('Invalid payment status')

            my_status = 'COMPLETED' if status == '1' else 'CANCELLED'
            selected_payment = Payment.objects.get(
                payment_intent=payment_intent,
                ephemeral_key=ephemeral_key,
            )
            selected_payment.status = status
            selected_payment.updated_at = timezone.now()
            selected_payment.save()

            # Unlocking all Courses
            all_courses = self.get_related_courses(user, None)
            for course in all_courses:
                self.unlock_first_level_mission(user, course)

            self.postSuccess({'Payment': my_status},
                             f'Payment has been {my_status} successfully!')
        except Exception as e:
            self.postError({'Payment': str(e)})
        return Response(self.output_object)

    def get(self, request, subs_id):
        try:
            # Get subscription
            subscription = get_object_or_404(Subscription, subs_id=subs_id)
            # Get user object
            user = SystemUser.objects.get(uid=request.headers['uid'])
            # Get customer_id
            stripe_cust_id = user.stripe_cust_id
            # Get ephemeralKey
            ephemeral_key = self.create_ephemeral_key(stripe_cust_id)
            # Get payment Intent
            payment_intent = self.create_payment_intent(
                stripe_cust_id, subscription)

            # Create new payment
            new_payment = Payment(
                subscription=subscription,
                user=user,
                ephemeral_key=ephemeral_key,
                payment_intent=payment_intent
            )
            new_payment.save()

            output = {
                'payment_sheet': {
                    'paymentIntent': payment_intent,
                    'ephemeralKey': ephemeral_key,
                    'customer': stripe_cust_id,
                    'publishableKey': settings.STRIPE['publishableKey']
                }
            }

            self.postSuccess(output, 'Sheet info collected successfully')
        except Exception as e:
            self.postError({'payment_sheet': str(e)})

        return Response(self.output_object)


class MissionApi(APIView, ApiResponse):
    authentication_classes = [RequestAuthentication, ]

    def __init__(self):
        ApiResponse.__init__(self)

    def unlock_next_cat(self, user_obj, current_category):
        next_cat = current_category.get_next_cat()
        if next_cat:
            print("next category found")
            print("Unlocking first course...")
            all_courses = Course.objects.filter(category=next_cat)
            if all_courses.count() > 0:
                print("First course exists")
                print("Unlocking first level and mission")
                self.unlock_first_level_mission(user_obj, all_courses[0])

    def unlock_next_course(self, user_obj, current_course_obj):
        next_course = current_course_obj.get_next_course()
        if next_course:
            print("Next course found")
            print("Unlocking first level and mission")
            self.unlock_first_level_mission(user_obj, next_course)
        else:
            print("Next course not found")
            print("Unlocking next category...")
            self.unlock_next_cat(user_obj, current_course_obj.category)

    def unlock_next_level(self, user_obj, current_level_obj):
        next_level = current_level_obj.get_next_level()
        if next_level:
            print("Next level found!")
            query = UnlockedLevel.objects.filter(
                user=user_obj, level=next_level)
            first_mission = Mission.objects.filter(level=next_level).first()
            if first_mission:
                url = f"mission/{first_mission.mission_id}"
            else:
                url = f"category/{next_level.course.category.cat_id}"

            if not query.exists():
                print("Next level unlocked")
                UnlockedLevel.objects.create(
                    level=next_level,
                    user=user_obj
                )

                if first_mission:
                    if not UnlockedMission.objects.filter(user=user_obj, mission=first_mission).exists():
                        UnlockedMission.objects.create(
                            mission=first_mission,
                            user=user_obj
                        )
            return {
                'message': 'Level completed',
                'button_text': 'Go next',
                'url': url
            }
        else:
            print("marking this course completed, since no next level exist")
            CompletedCourse.objects.create(
                course=current_level_obj.course,
                user=user_obj
            )
            print("course marked as completed")
            return {
                'message': 'Course completed',
                'button_text': 'Explore more courses',
                'url': f'category/{current_level_obj.course.category.cat_id}'
            }
            # print("Unlocking next course...")
            # self.unlock_next_course(user_obj, current_level_obj.course)

    def unlock_next_mission(self, user_obj, current_mission_obj):
        next_mission = current_mission_obj.get_next_mission()
        if next_mission:
            print("next mission FOUND...")
            # Check if not already exists
            query = UnlockedMission.objects.filter(
                user=user_obj, mission=next_mission)
            if not query.exists():
                UnlockedMission.objects.create(
                    mission=next_mission,
                    user=user_obj
                )
            print("Unlocked next mission")
            return {
                'message': 'Mission completed',
                'button_text': 'Go next',
                'url': f'mission/{next_mission.mission_id}'
            }
        else:
            print("next mission not FOUND...")
            # Current mission is the last mission, its mean level is completed
            # Marking level as completed
            print("Marking this level as COMPLETED...")
            unlocked_level = UnlockedLevel.objects.get(
                user=user_obj, level=current_mission_obj.level)
            unlocked_level.is_completed = True
            unlocked_level.save()

            if (user_obj.is_trial_taken and not user_obj.is_trial_end) or (user_obj.is_fee_paid):
                print("Unlocking next level...")
                return self.unlock_next_level(user_obj, current_mission_obj.level)
            else:
                print("Purchase a plan to access the full course!")
                return {
                    'message': 'Want full access of the content?',
                    'button_text': 'Unlock courses',
                    'url': 'subscriptions'
                }

    def check_access(self, mission, uid):
        user_obj = SystemUser.objects.get(uid=uid)
        query = UnlockedMission.objects.filter(
            user=user_obj,
            mission=mission
        )

        if query.exists():
            # current_level = mission.level
            # Marking mission as COMPLETED
            unlocked_mission = query[0]
            unlocked_mission.is_completed = True
            unlocked_mission.save()
            print("Unlocking next mission...")
            return self.unlock_next_mission(user_obj, unlocked_mission.mission)
        return False

    def get(self, request, mission_id=None):
        if not mission_id:
            self.postError({'mission_id': 'Mission id is missing'})
            return Response(self.output_object)
        try:
            user = SystemUser.objects.get(uid=request.headers['uid'])
            single_mission = Mission.objects.get(mission_id=mission_id)
            access_result = self.check_access(
                single_mission, request.headers['uid'])
            if not access_result:
                self.postError({'mission': 'This mission is locked'})
                return Response(self.output_object)
            # Adding visit
            last_visit_object = LastVisit.objects.update_or_create(
                user=user,
                defaults={'mission': single_mission}
            )

            serializer = MissionDetailSerializer(single_mission, many=False)
            full_data = {
                'mission': serializer.data,
                'next': access_result
            }

            self.postSuccess(full_data, "Mission fetched successfully")
        except Exception as e:
            self.postError({'mission': str(e)})
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


class UserApi(APIView, ApiResponse):
    authentication_classes = [RequestAuthentication]

    def __init__(self):
        ApiResponse.__init__(self)

    def post(self, request, uid=None):
        try:
            data = request.data.copy()
            stripe_cust_id = self.create_stripe_user(data)
            data['stripe_cust_id'] = stripe_cust_id
            data['uid'] = uid
            serializer = UserSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                user = SystemUser.objects.get(uid=uid)
                self.postSuccess({'user': serializer.data},
                                 "User added successfully")
            else:
                self.delete_stripe_user(stripe_cust_id)
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

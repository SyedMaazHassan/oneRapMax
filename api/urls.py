from django.urls import path
from . import views
from api.views import *
from django.conf import settings
from django.conf.urls.static import static

# from rest_framework_simplejwt.views import (
#     TokenObtainPairView,
#     TokenRefreshView,
# )

urlpatterns = [
    path('', views.index, name="index"),
    # GET API
    # Badge api

    path('search', UserSearchApi.as_view()),

    path('goal', GoalApi.as_view()),

    path('achievement', AchievementApi.as_view()),

    path('user', AllUserApi.as_view()),
    path('user/<uid>', UserApi.as_view()),

    path('user/<uid>/add', UserApi.as_view()),
    path('user/<uid>/update', UserApi.as_view()),

    path('user/<uid>/update', UserApi.as_view()),

    # Muscles
    path('muscles', MuscleApi.as_view()),
    path('muscles/<muscle_id>', MuscleApi.as_view()),

    path('muscles/<muscle_id>/exercise/<exercise_id>', ExerciseApi.as_view()),

    path('exercise', AllExerciseApi.as_view()),

    path('leaderboard',
         LeaderBoard.as_view()),

    path('group/create', GroupApi.as_view()),
    path('group/<id>/delete', GroupApi.as_view()),
    path('group', GroupApi.as_view())

]


urlpatterns = urlpatterns + \
    static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

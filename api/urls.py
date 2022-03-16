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
    path('', views.index, name="index"),

    path('user/', UserApi.as_view()),
    path('user/<uid>', UserApi.as_view()),

    path('user/<uid>/add', UserApi.as_view()),
    path('user/<uid>/update', UserApi.as_view()),

    path('user/<uid>/update', UserApi.as_view()),

    # Muscles
    path('muscles', MuscleApi.as_view()),
    path('muscles/<muscle_id>', MuscleApi.as_view()),

    path('muscles/<muscle_id>/exercise/<exercise_id>', ExerciseApi.as_view()),

    path('muscles/<muscle_id>/exercise/<exercise_id>/leaderboard',
         LeaderBoard.as_view()),

    # path('categories', CategoryApi.as_view()),
    # path('category/', CategoryApi.as_view()),
    # path('category/<cat_id>', CategoryApi.as_view()),

    # path('level/', LevelApi.as_view()),
    # path('level/<level_id>', LevelApi.as_view()),

    # path('mission/', MissionApi.as_view()),
    # path('mission/<mission_id>', MissionApi.as_view()),

    # path('subscriptions', SubscriptionApi.as_view()),
    # path('subscription/', SubscriptionApi.as_view()),
    # path('subscription/<subs_id>', SubscriptionApi.as_view()),
    # path('subscription/<subs_id>/start-trial', SubscriptionApi.as_view()),


    # path('subscription/<subs_id>/payment-info', PaymentApi.as_view()),

    # path('payment', PaymentApi.as_view())
    # path('auth/checktoken', AuthenticationApi.as_view()),
    # path('auth/<action>', AuthenticationApi.as_view()),

    # path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # path('scripts/', GetParticularScriptApi.as_view()),
    # path('get-employees/', GetEmployeeApi.as_view()),
    # path('save-employee/', SaveEmployeeApi.as_view()),
    # path('update-employee/', UpdateEmployeeApi.as_view()),
    # path('delete-employee/', DeleteEmployeeApi.as_view()),
    # path('undelete-employee/', UndeleteEmployeeApi.as_view()),
    # path('get-company-info/', GetCompanyApi.as_view()),
    # path('update-company-info/', UpdateCompanyApi.as_view()),

]


urlpatterns = urlpatterns + \
    static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.urls import path, include

from . import views

urlpatterns = [
    path('races/', include([
        path('', views.RacesView.as_view()),
        path('<str:id>/', include([
            path('', views.RaceView.as_view()),
            path('follow/', views.FollowRaceView.as_view()),
            path('unfollow/', views.UnfollowRaceView.as_view()),
        ])),
    ])),
]

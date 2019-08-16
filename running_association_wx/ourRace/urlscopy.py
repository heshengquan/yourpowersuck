from django.urls import path, include

from ourRace import views

urlpatterns = [
    path('our-races/', include([
        path('', views.MarathonsView.as_view()),#马拉松列表
        path('participation-info/', views.ParticipationInfoView.as_view()),#报名
        path('info/<str:infoid>/', views.MarathonInfoView.as_view()),#马拉松章程信息
        path('<str:id>/', include([
            path('', views.MarathonView.as_view()),#具体马拉松参与人员信息
            path('extra/', views.MarathonExtraInfoView.as_view()),#额外信息，用户分舵等
            path('competition-events/', include([
                path('', views.CompetitionEventsView.as_view()),#马拉松项目列表
                path('<str:evid>/', views.CompetitionEventView.as_view()),#项目的详细信息
            ])),
            path('sign-up/<str:evid>/', views.MarathonSignUpView.as_view()),#支付
        ])),
    ])),
]

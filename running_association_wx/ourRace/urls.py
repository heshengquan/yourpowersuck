from django.urls import path, include

from ourRace import views

urlpatterns = [
    path('our-races/', include([
        path('', views.MarathonsView.as_view()),
        path('participation-info/', views.ParticipationInfoView.as_view()),
        path('info/<str:infoid>/', views.MarathonInfoView.as_view()),
        path('ao-number-search/', views.AoNumberSearch.as_view()),
        path('<str:id>/', include([
            path('', views.MarathonView.as_view()),
            path('extra/', views.MarathonExtraInfoView.as_view()),
            path('competition-events/', include([
                path('', views.CompetitionEventsView.as_view()),
                path('<str:evid>/', views.CompetitionEventView.as_view()),
            ])),
            path('sign-up/<str:evid>/', views.MarathonSignUpView.as_view()),
        ])),
        path('<str:prepay_id>/order-success-result/', views.MarathonOrderSuccessView.as_view())
    ])),
]

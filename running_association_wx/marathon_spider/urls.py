from django.urls import path, include

from . import views

urlpatterns = [
    path('marathons/', include([
        path('query/', views.MarathonQueryView.as_view()),
        path('display/<str:id>/', include([
            path('', views.MarathonsDisplayView.as_view()),
            path('personal-best/', views.MarathonsPersonalBestDisplayView.as_view()),
        ])),
        path('ranking/', views.MarathonRankingView.as_view()),
        path('my-ranking/', views.MyMarathonRankingView.as_view()),
        path('record-city/', views.RecordMemberMarathonCity.as_view()),

    ])),
]

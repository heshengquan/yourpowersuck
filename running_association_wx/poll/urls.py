from django.urls import path, include

from . import views

urlpatterns = [
    path('polling-activities/', include([
        path('', views.PollingActivitiesView.as_view()),
        path('<str:id>/', include([
            path('', views.PollingActivityView.as_view()),
            path('nearby-polling-items/',views.NearbyPollingItemsView.as_view()),
            path('ranking/', views.PollingItemsRankingView.as_view()),
            path('city-ranking/', views.PollingItemsCityRankingView.as_view()),
            path('city-polling-items/',views.CityPollingItemsView.as_view()),
            path('create-item/', views.CreatePollingItemView.as_view()),
            path('lucky-draw-result/',views.LuckyDrawResultView.as_view()),
            path('my-polling-status/',views.MyPollingStatusView.as_view()),
            path('get_all/', views.GetAllView.as_view()),
        ])),
    ])),
    path('polling-items/', include([
        path('<str:id>/', include([
            path('add-item/', views.AddPollingItemView.as_view()),
            path('add-item-images/', views.AddPollingItemImagesView.as_view()),
            path('delete-item-images/', views.DeletePollingItemImagesView.as_view()),
            path('detail/', views.PollingItemView.as_view()),
            path('detail-images/',views.PollingItemImagesView.as_view()),
            path('participate-poll/',views.ParticipatePollView.as_view()),
            path('detail-info/',views.AddVotesAutoView.as_view()),
            path('two-bar-codes/', views.GetTwoBarCodesView.as_view()),
            path('join-item/', views.JoinPollingItemView.as_view()),
        ])),
    ])),
]

from django.urls import path, include

from . import views

urlpatterns = [
    path('activities/<str:id>/', include([
        path('', views.ActivityView.as_view()),
        path('member-avatar-urls/', views.ActivityMemberAvatarURLsView.as_view()),
        path('members/', include([
            path('', views.ActivityMembersView.as_view()),
            path('extra-info/', views.ActivityMembersExtraInfoView.as_view()),
        ])),
        path('edit/', views.ActivityEditView.as_view()),
        path('edit-image/', views.ActivityEditImageView.as_view()),
        path('edit-status/', views.ActivityEditStatusView.as_view()),
        path('join/', views.JoinActivityView.as_view()),
        path('quit/', views.QuitActivityView.as_view()),
        path('delete/', views.DeleteActivityView.as_view()),
        path('upload-pic/', views.UploadActivityPicView.as_view()),
        path('activityImages/',views.GetActivityImages.as_view()),
        path('delete-activity-image/',views.DeleteActivityImageView.as_view()),
        path('<str:option>/', views.SignInOrSignOutView.as_view()),
    ]))
]

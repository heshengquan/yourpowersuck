from django.urls import path, include

from . import views

urlpatterns = [
    path('wx/', include([
        path('login/', views.WXLoginView.as_view()),
        path('authorization/', include([
            path('user-info/', views.WXAuthorizationUserInfoView.as_view()),
            path('mobile/', views.WXAuthorizationMobileView.as_view()),
        ])),
        path('access-token/', views.GetAccessTokenView.as_view()),
    ])),
    path('members/', include([
        path('get-form-id/',views.GetFormIdView.as_view()),
        path('edit-name/', views.MemberEditView.as_view()),
        path('edit-avatar/', views.MemberEditView.as_view()),
        path('edit-mobile/', views.MemberEditMobileView.as_view()),
        path('check-mobile/', views.MemberCheckMobileView.as_view()),
        path('start-branch/', views.MemberStartBranchView.as_view()),
        path('<str:id>/', include([
            path('showing/', views.MemberShowingView.as_view()),
            path('profile', views.MemberProfileView.as_view()),
            path('sticky-activity/', views.MemberStickyActivityView.as_view()),
            path('activities/', include([
                path('', views.MemberActivitiesView.as_view()),
                path('extra-info/', views.MemberActivitiesExtraInfoView.as_view()),
            ])),
            path('branch-id/', views.MemberBranchIdView.as_view()),
            path('is-runner/', views.MemberIsRunnerView.as_view()),
            path('nearby-activities/', views.NearbyActivitiesView.as_view()),
        ])),
    ])),
]

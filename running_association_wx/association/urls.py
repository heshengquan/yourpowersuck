from django.urls import path, include

from . import views

urlpatterns = [
    path('branches/', include([
        path('', views.BranchesView.as_view()),
        path('<str:id>/', include([
            path('', views.BranchView.as_view()),
            path('member-avatar-urls/', views.BranchMemberAvatarURLsView.as_view()),
            path('activities/', views.BranchActivitiesView.as_view()),
            path('members/', include([
                path('', views.BranchMembersView.as_view()),
                path('extra-info/', views.BranchMembersExtraInfoView.as_view()),
            ])),
            path('join/', views.JoinBranchView.as_view()),
            path('quit/', views.QuitBranchView.as_view()),
            path('start-activity/', views.BranchStartActivityView.as_view()),
            path('delete/', views.DeleteBranchView.as_view()),
            path('edit/', views.BranchEditView.as_view()),
            path('edit-location/', views.BranchEditLocationView.as_view()),
            path('transfer-authority/', views.BranchTransferAuthority.as_view()),
            path('edit-image/', views.BranchEditImageView.as_view()),
            path('donate-fund/', views.MemberDonateFund.as_view()),
            path('withdraw-fund/', views.MasterWithDrawFund.as_view()),
            path('fund-detail/', views.ShowBranchFundDetail.as_view()),
            path('fund-ranking/', views.ShowBranchFundRanking.as_view()),
            path('<str:option>/', views.SetOrUnsetDeputyView.as_view()),  # 会匹配到所有id后面加一个字符串的链接
        ])),
    ]))
]

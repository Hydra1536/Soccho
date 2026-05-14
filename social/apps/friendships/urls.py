from django.urls import path

from apps.friendships.views import AcceptRequestView, ListFriendsView, RejectRequestView, SendRequestView

urlpatterns = [
    path('send-request/', SendRequestView.as_view(), name='send-request'),
    path('accept/', AcceptRequestView.as_view(), name='accept-friend-request'),
    path('reject/', RejectRequestView.as_view(), name='reject-friend-request'),
    path('list/', ListFriendsView.as_view(), name='list-friends'),
    path('friends/', ListFriendsView.as_view(), name='friends'),
]

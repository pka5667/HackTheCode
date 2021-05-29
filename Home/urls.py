from django.conf.urls import url

from . import views
from django.urls import path, include

urlpatterns = [
    path('', views.index, name="home"),
    path('about', views.about, name="about"),
    path('contact', views.contact, name="contact"),
    path('contest/<str:contestId>', views.contestPageHandler, name="contest"),
    path('practice', views.practiceContestPageHandler, name="practice"),
    path('problem/<str:contestId>/<str:problemId>', views.problemPageHandler, name="problem"),
    path('submit/<str:contestId>/<str:problemId>', views.handleCodeSubmision, name="submit"),
    path('leaderboard/<str:contestId>', views.leaderBoardPageHandler, name="leaderboard"),
    path('profile/<str:userName>', views.profilePageHandler, name="profile"),
    path('logout', views.handleLogout, name="logout")
]

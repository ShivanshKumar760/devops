# blog/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path("auth/register/", views.register,    name="register"),
    path("auth/login/",    views.login,       name="login"),

    # Posts
    path("posts/",         views.post_list,   name="post-list"),
    path("posts/<int:pk>/", views.post_detail, name="post-detail"),
]
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("utilisateurs/", views.user_list, name="user_list"),
    path("utilisateurs/nouveau/", views.user_create, name="user_create"),
    path("utilisateurs/<int:pk>/modifier/", views.user_edit, name="user_edit"),
]

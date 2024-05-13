from django.urls import path
from . import views

urlpatterns = [ 
    path("", views.index, name = "index"),
    path("dashboard.html/", views.dashboard, name = "dashboard"),
    path("sign_in.html/", views.sign_in, name = "sign-in"),
]

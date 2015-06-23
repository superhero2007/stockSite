from django.conf.urls import url 

from . import views

urlpatterns = [ 
    url(r'^$', views.login_view, name='index'),
    url(r'^login/$', views.login_view, name='user_login'),
    url(r'^logout/$', views.logout_view, name='user_logout'),
]

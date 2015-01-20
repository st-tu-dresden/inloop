from django.conf.urls import patterns, url
from home import views

urlpatterns = patterns('',
                       url(r'^index/', views.index, name='index'),
                       url(r'^about/', views.about, name='about'),
                       url(r'^impressum/', views.impressum, name='impressum'),
                       url(r'^.*$', views.index, name='index'),
)

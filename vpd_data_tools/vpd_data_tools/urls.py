from django.conf.urls import patterns, include, url
from django.contrib.gis import admin

urlpatterns = patterns('',
    url(r'^dashboard/', 'rms.views.dashboard', name='dashboard'),
    url(r'^arrival_time/', 'rms.views.arrival_time', name='arrival_time'),
    url(r'^where/', 'rms.views.routes', name='routes'),
    url(r'^timing/', 'rms.views.timing', name='timing'),
    url(r'^lobby_creates/', 'rms.views.lobby_creates', name='lobby_creates'),
    url(r'^admin/', include(admin.site.urls)),
)

from django.conf.urls import patterns, url
from core.views import HomeTemplateView

urlpatterns = patterns('',
    url(r'^$', HomeTemplateView.as_view(), name='home'),
)
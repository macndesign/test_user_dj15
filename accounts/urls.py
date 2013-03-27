from django.conf.urls import patterns, url
from django.views.generic import TemplateView
from accounts.forms import UserAuthenticationForm
from accounts.views import register, activate, profile

urlpatterns = patterns('',
                       url(r'^activate/complete/$',
                           TemplateView.as_view(template_name="accounts/activation_complete.html"),
                           name='registration_activation_complete'),
                       # Activation keys get matched by \w+ instead of the more specific
                       # [a-fA-F0-9]{40} because a bad activation key should still get to the view;
                       # that way it can return a sensible "invalid key" message instead of a confusing 404.
                       url(r'^activate/(?P<activation_key>\w+)/$', activate, name='registration_activate'),
                       url(r'^register/$', register, name='registration_register'),
                       url(r'^register/complete/$',
                           TemplateView.as_view(template_name="accounts/registration_complete.html"),
                           name='registration_complete'),

                       # Auth urls
                       url(r'^login/$', 'django.contrib.auth.views.login',
                           {'template_name': 'accounts/login.html',
                            'authentication_form': UserAuthenticationForm}, name='auth_login'),
                       url(r'^logout/$', 'django.contrib.auth.views.logout', name='auth_logout'),
                       url(r'^password/change/$', 'django.contrib.auth.views.password_change',
                           name='auth_password_change'),
                       url(r'^password/change/done/$', 'django.contrib.auth.views.password_change_done',
                           name='auth_password_change_done'),
                       url(r'^password/reset/$', 'django.contrib.auth.views.password_reset',
                           name='auth_password_reset'),
                       url(r'^password/reset/done/$', 'django.contrib.auth.views.password_reset_done',
                           name='auth_password_reset_done'),
                       url(r'^reset/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
                           'django.contrib.auth.views.password_reset_confirm',
                           name='auth_password_reset_confirm'),
                       url(r'^reset/done/$', 'django.contrib.auth.views.password_reset_complete',
                           name='auth_password_reset_complete'),

                       # Profile
                       url(r'^profile/$', profile),
)
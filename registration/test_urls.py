"""
URLs used in the unit tests for django-registration-email.
"""

from django.conf.urls import patterns, include, url

from registration.views import activate, register

js_info_dict = {
    'domain': 'djangojs',
    'packages': 'registration_email',
}

urlpatterns = patterns('',
                       url(r'^i18n/', include('django.conf.urls.i18n')),
                       url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict),)

urlpatterns += patterns('',

                        # Test the'register' view with extra_context argument.
                        url(r'^register-extra-context/$',
                            register,
                            {'extra_context': {'foo': 'bar', 'callable': lambda: 'called'}, },
                            name='registration_test_register_extra_context'),

                        # Test the 'register' view with custom redirect on successful registration.
                        url(r'^register-with-success_url/$',
                            register,
                            {'success_url': 'registration_register', },
                            name='registration_test_register_success_url'
                        ),

                        # Test the 'activate' view with extra_context_argument.
                        url(r'^activate-extra-context/(?P<activation_key>\w+)/$',
                            activate,
                            {'extra_context': {'foo': 'bar', 'callable': lambda: 'called'}, },
                            name='registration_test_activate_extra_context'),

                        # Test the 'activate' view with success_url argument.
                        url(r'^activate-with-success-url/(?P<activation_key>\w+)/$',
                            activate,
                            {'success_url': 'registration_register', },
                            name='registration_test_activate_success_url'),

                        # Default urls
                        (r'', include('registration.urls')),
)
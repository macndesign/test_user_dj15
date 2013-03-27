from accounts.forms import UserCreationForm
from accounts.models import User
from django.template import RequestContext
from django.shortcuts import redirect
from django.shortcuts import render_to_response
from django.contrib.auth import login
from django.conf import settings
from accounts import signals


def register(request, success_url='registration_complete',
             template_name='accounts/registration_form.html',
             extra_context=None):
    """
    Allow a new user to register an account.
    """

    if request.method == 'POST':
        form = UserCreationForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            new_user = User.objects.create_inactive_user(cleaned_data['email'], cleaned_data['password1'])
            signals.user_registered.send(sender=User,
                                         user=new_user,
                                         request=request)
            return redirect(success_url)
    else:
        form = UserCreationForm()

    if extra_context is None:
        extra_context = {}
    context = RequestContext(request)
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value

    return render_to_response(template_name,
                              {'form': form},
                              context_instance=context)


def activate(request, activation_key, template_name='accounts/activate.html',
             success_url=None, extra_context=None, **kwargs):
    """
    Activate a user's account.
    """

    activated = User.objects.activate_user(activation_key)
    if activated:
        signals.user_activated.send(sender=User,
                                    user=activated,
                                    request=request)

        if settings.AUTHENTICATE_WHEN_ACTIVATE:
            activated.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, activated)

        if success_url is None:
            return redirect('registration_activation_complete', **kwargs)
        else:
            return redirect(success_url)

    if extra_context is None:
        extra_context = {}
    context = RequestContext(request)
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value

    return render_to_response(template_name,
                              kwargs,
                              context_instance=context)

def profile(request):
    return render_to_response('accounts/profile.html', {'user': request.user}, context_instance=RequestContext(request))
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from accounts.models import User
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm


class UserCreationForm(forms.ModelForm):
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }

    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    if getattr(settings, 'ADD_TOS', False):
        tos = forms.BooleanField(widget=forms.CheckboxInput(),
                                 label=_(u'I have read and agree to the Terms of Service'),
                                 error_messages={'required': _("You must agree to the terms to register")})

    if getattr(settings, 'ADD_RECAPTCHA', False):
        from captcha.fields import ReCaptchaField
        captcha = ReCaptchaField(attrs={'theme': 'custom', 'custom_theme_widget': 'recaptcha_widget'})

    class Meta:
        model = User
        fields = ('email',)

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'])
        return password2

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(label=_("Password"),
                                         help_text=_("Raw passwords are not stored, so there is no way to see "
                                                     "this user's password, but you can change the password "
                                                     "using <a href=\"password/\">this form</a>."))

    class Meta:
        model = User

    def clean_password(self):
        return self.initial["password"]


class UserAuthenticationForm(AuthenticationForm):
    error_messages = {
        'invalid_login': _(
            "Please re-enter your password. The password you entered is incorrect. Please try again (make sure your "
            "caps lock is off)."),
        'no_cookies': _("Your Web browser doesn't appear to have cookies "
                        "enabled. Cookies are required for logging in."),
        'inactive': _("This account is inactive."),
    }


class AdminUserCreationForm(forms.ModelForm):
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }

    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', )

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'])
        return password2

    def save(self, commit=True):
        user = super(AdminUserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

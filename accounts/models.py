import hashlib
import random
import re
import datetime
from django.db import models
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.utils.http import urlquote
from django.core.mail import send_mail, EmailMultiAlternatives
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.conf import settings
from django.template.loader import render_to_string

SHA1_RE = re.compile('^[a-f0-9]{40}$')


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        now = timezone.now()
        if not email:
            raise ValueError(_('Users must have an email address'))

        user = self.model(
            email=UserManager.normalize_email(email),
            is_staff=False, is_active=True, is_superuser=False,
            last_login=now, date_joined=now, **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        user = self.create_user(email, password=password, **extra_fields)
        user.is_staff = True
        user.is_active = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

    def create_inactive_user(self, email, password, send_email=True, **extra_fields):
        user = self.create_user(email, password, **extra_fields)
        user.is_active = False

        salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        if isinstance(email, unicode):
            email = email.encode('utf-8')
        user.activation_key = hashlib.sha1(salt + email).hexdigest()

        user.save(using=self._db)

        if send_email:
            site = Site.objects.get_current()
            self.send_activation_email(user, site)

        return user

    def activate_user(self, activation_key):
        if SHA1_RE.search(activation_key):
            try:
                user = self.get(activation_key=activation_key)
            except self.model.DoesNotExist:
                return False
            if not user.activation_key_expired():
                user.is_active = True
                user.activation_key = self.model.ACTIVATED
                user.save()
                return user
        return False

    def send_activation_email(self, user, site):
        ctx_dict = {'activation_key': user.activation_key,
                    'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
                    'site': site,
                    'static_url': settings.STATIC_URL}

        subject = render_to_string('accounts/activation_email_subject.txt', ctx_dict)
        subject = ''.join(subject.splitlines())

        message_text = render_to_string('accounts/activation_email.txt', ctx_dict)
        message_html = render_to_string('accounts/activation_email.html', ctx_dict)

        msg = EmailMultiAlternatives(subject, message_text, settings.DEFAULT_FROM_EMAIL, [user.email])
        msg.attach_alternative(message_html, "text/html")
        msg.send()


class User(AbstractBaseUser, PermissionsMixin):
    ACTIVATED = u"ALREADY_ACTIVATED"

    email = models.EmailField(verbose_name=_('email address'), max_length=255, unique=True, db_index=True)
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    is_staff = models.BooleanField(_('staff status'), default=False,
                                   help_text=_('Designates whether the user can log into this admin '
                                               'site.'))
    is_active = models.BooleanField(_('active'), default=True,
                                    help_text=_('Designates whether this user should be treated as '
                                                'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    activation_key = models.CharField(_('activation key'), max_length=40, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_absolute_url(self):
        return "/users/%s/" % urlquote(self.email)

    def email_user(self, subject, message, from_email=None):
        send_mail(subject, message, from_email, [self.email])

    def get_full_name(self):
        if self.first_name and self.last_name:
            full_name = '%s %s' % (self.first_name, self.last_name)
        elif self.first_name:
            full_name = self.first_name
        else:
            full_name = self.email

        return full_name.strip()

    def get_short_name(self):
        if self.first_name:
            short_name = self.first_name
        elif self.last_name:
            short_name = self.last_name
        else:
            short_name = self.email

        return short_name.strip()

    def activation_key_expired(self):
        expiration_date = datetime.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS)
        return self.activation_key == self.ACTIVATED or (self.date_joined + expiration_date <= timezone.now())

    activation_key_expired.boolean = True

    def __unicode__(self):
        return self.email

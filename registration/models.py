# -*- coding: utf-8 -*-
import datetime
import hashlib
import random
import re

from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.sites.models import RequestSite, Site
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings

SHA1_RE = re.compile('^[a-f0-9]{40}$')


class EldonUserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        now = timezone.now()
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(email=email,
                          is_staff=False, is_active=True, is_superuser=False,
                          last_login=now, date_joined=now, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Creates and saves inactive User with the given email and password.        
        """        
        u = self.create_user(email, password, **extra_fields)
        u.is_staff = True
        u.is_active = True
        u.is_superuser = True
        u.save(using=self._db)
        return u        

    def create_inactive_user(self, email, password, send_email=True, **extra_fields):
        """
        Creates and saves inactive User with the given email and password.        
        """        
        u = self.create_user(email, password, **extra_fields)
        u.is_active = False

        #salt
        salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        if isinstance(email, unicode):
            email = email.encode('utf-8')
        u.activation_key = hashlib.sha1(salt + email).hexdigest()

        u.save(using=self._db)

        #send activation email
        if send_email:
            if Site._meta.installed:
                site = Site.objects.get_current()
            else:
                site = RequestSite(request)     
                       
            self.send_activation_email(u, site)

        return u        

    create_inactive_user = transaction.commit_on_success(create_inactive_user)

    def activate_user(self, activation_key):
        """
        Validate an activation key and activate the corresponding User if valid.
        """
        # Make sure the key we're trying conforms to the pattern of a
        # SHA1 hash; if it doesn't, no point trying to look it up in
        # the database.
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
        """
        Send an activation email to the user associated with this User object.          
        """

        ctx_dict = {'activation_key': user.activation_key,
                    'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
                    'site': site,
                    'static_url': settings.STATIC_URL}

        subject = render_to_string('registration/activation_email_subject.txt',
                                   ctx_dict)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        
        message_text = render_to_string('registration/activation_email.txt', ctx_dict)
        message_html = render_to_string('registration/activation_email.html', ctx_dict)

        msg = EmailMultiAlternatives(subject, message_text, settings.DEFAULT_FROM_EMAIL, [user.email])
        msg.attach_alternative(message_html, "text/html")
        msg.send()


class EldonUser(AbstractBaseUser, PermissionsMixin):
    """
        Define custom User class and override Django's one.
        In this class the unique identifier for the user is his email adress.
    """

    ACTIVATED = u"ALREADY_ACTIVATED"

    email = models.EmailField(_('email adress'), unique=True, db_index=True)
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    is_staff = models.BooleanField(_('staff status'), default=False, help_text=_('Designates whether the user can log '
                                                                                 'into this admin site.'))
    is_active = models.BooleanField(_('is_active?'), default=True, help_text=_('Designates whether this user should be '
                                                                               'treated as active. Unselect this '
                                                                               'instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    activation_key = models.CharField(_('activation key'), max_length=40, blank=True)

    objects = EldonUserManager()

    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __unicode__(self):
        return self.get_short_name()

    def get_full_name(self):
        """
            Returns the first_name plus the last_name, with a space in between.
            or if the both fist and last name are not provided, return email
        """
        if self.first_name or self.last_name:
            full_name = '%s %s' % (self.first_name, self.last_name)
        else:
            full_name = self.email

        return full_name.strip()

    def get_short_name(self):
        """
            Returns the first_name or email if the first is not provided
        """
        if self.first_name:
            short_name = self.first_name
        elif self.last_name:
            short_name = self.last_name
        else:
            short_name = self.email

        return short_name.strip()

    def email_user(self, subject, message, from_email=None):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email])

    def activation_key_expired(self):
        """
        Determine whether this EldonUser's activation key has expired
        """
        expiration_date = datetime.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS)
        return self.activation_key == self.ACTIVATED or (self.date_joined + expiration_date <= timezone.now())
    activation_key_expired.boolean = True

    def has_perm(self, perm, obj=None):
        """Does the user have a specific permission?"""
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        """Does the user have permissions to view the app `app_label`?"""
        # Simplest possible answer: Yes, always
        return True

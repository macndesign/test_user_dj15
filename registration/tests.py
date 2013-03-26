import datetime

from django.core.urlresolvers import reverse
from django.core import mail
from django.test import TestCase
from django.conf import settings

from registration.forms import UserCreationForm
from registration.models import EldonUser

class RegistrationTests(TestCase):
    """
    Test the registration views and models.
    """

    urls = 'registration_withemail.test_urls'
    ACTIVATED = u"ALREADY_ACTIVATED"

    def create_user(self):
        return self.client.post(reverse('registration_register'),
                                data={'email': 'foofoo@barbar.com',
                                      'password1': 'secret',
                                      'password2': 'secret',
                                      'tos': 'on'})

    def test_registration_view_initial(self):
        """
        Render the registration template.
        """
        response = self.client.get(reverse('registration_register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/registration_form.html')
        self.assertTrue(isinstance(response.context['form'], UserCreationForm))

    def test_registration_view_success(self):
        """
        Register a new user.
        """
        response = self.create_user()

        self.assertRedirects(response, reverse('registration_complete'))
        self.assertEqual(EldonUser.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_registration_view_failure(self):
        '''
        New user registration failed
        '''
        response = self.client.post(reverse('registration_register'), {'email':'foo@bar.com', 
                                                                       'password1':'secret', 
                                                                       'password2':'Iknowit',
                                                                       'tos':'on'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form'].is_valid(), False)
        self.assertFormError(response, 'form', field='password2',
                             errors=u"The two password fields didn't match.")
        self.assertEqual(len(mail.outbox), 0) 

    def test_registration_extra_context(self):
        """
        Test extra context
        """
        response = self.client.get(reverse('registration_test_register_extra_context'))
        self.assertEqual(response.context['foo'], 'bar')
        self.assertEqual(response.context['callable'], 'called')

    def test_registration_success_url(self):
        """
        Test extra param redirection
        """
        response = self.client.post(reverse('registration_test_register_success_url'),
                                    data={'email': 'foobar@foobar.com',
                                          'password1': 'secret',
                                          'password2': 'secret',
                                          'tos': 'on'})

        user = EldonUser.objects.get(email='foobar@foobar.com')
        self.assertFalse(user.is_active)        

        self.assertRedirects(response, reverse('registration_register'))        


    def test_valid_activation(self):
        self.create_user()
        
        user = EldonUser.objects.get(email='foofoo@barbar.com')
        response = self.client.get(reverse('registration_activate', kwargs={'activation_key' : user.activation_key}))


        user = EldonUser.objects.get(email='foofoo@barbar.com')
        self.assertEqual(user.activation_key, self.ACTIVATED)
        self.assertTrue(user.is_active)
        self.assertRedirects(response, reverse('registration_activation_complete'))

    def test_invalid_activation_key(self):
        self.create_user()
        
        user = EldonUser.objects.get(email='foofoo@barbar.com')
        response = self.client.get(reverse('registration_activate', kwargs={'activation_key' : 'invalid_key'}))

        user = EldonUser.objects.get(email='foofoo@barbar.com')
        self.assertNotEqual(user.activation_key, self.ACTIVATED)
        self.assertFalse(user.is_active)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('registration/activate.html')
        
    def test_activation_expired_key(self):
        self.create_user()

        user = EldonUser.objects.get(email='foofoo@barbar.com')
        user.date_joined = user.date_joined - datetime.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS+1)
        user.save()

        response = self.client.get(reverse('registration_activate', kwargs={'activation_key' : user.activation_key}))
        user = EldonUser.objects.get(email='foofoo@barbar.com')

        self.assertFalse(user.is_active)
        self.assertNotEqual(user.activation_key, self.ACTIVATED)        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('registration/activate.html')

    def test_activation_extra_context(self):
        """
        Test extra context
        """
        self.create_user()
        
        user = EldonUser.objects.get(email='foofoo@barbar.com')
        response = self.client.get(reverse('registration_test_activate_extra_context', kwargs={'activation_key' : 'bar'}))
        self.assertEqual(response.context['foo'], 'bar')
        self.assertEqual(response.context['callable'], 'called')        


    def test_activation_success_url(self):
        """
        Test extra param redirection
        """
        self.create_user()
        
        user = EldonUser.objects.get(email='foofoo@barbar.com')
        response = self.client.get(reverse('registration_test_activate_success_url', kwargs={'activation_key' : user.activation_key}))
        self.assertRedirects(response, reverse('registration_register'))
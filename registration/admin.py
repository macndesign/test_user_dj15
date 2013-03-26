from django.contrib import admin, messages
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin
from django.contrib.sites.models import RequestSite, Site
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_post_parameters
from django.shortcuts import get_object_or_404
from django.utils.html import escape
from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect
from registration.forms import AdminUserCreationForm, UserChangeForm
from registration.models import EldonUser


class EldonUserAdmin(UserAdmin):
    # The forms to add and change user instances
    form = UserChangeForm
    add_form = AdminUserCreationForm

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    actions = ['activate_users', 'resend_activation_email']
    list_display = ('email', 'is_superuser')
    list_filter = ('is_superuser',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_superuser',)}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = ((None, {'classes': ('wide',), 'fields': ('email', 'password1', 'password2')}
),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()

    def activate_users(self, request, queryset):
        """
        Activates the selected users, if they are not alrady activated.
        """
        for user in queryset:
            EldonUser.objects.activate_user(user.activation_key)
    activate_users.short_description = _("Activate users")

    def resend_activation_email(self, request, queryset):
        """
        Re-sends activation emails for the selected users.
        """
        if Site._meta.installed:
            site = Site.objects.get_current()
        else:
            site = RequestSite(request)

        for user in queryset:
            if not user.activation_key_expired():
                user.send_activation_email(site)
    resend_activation_email.short_description = _("Re-send activation emails")

    @sensitive_post_parameters()
    def user_change_password(self, request, id, form_url=''):
        if not self.has_change_permission(request):
            raise PermissionDenied
        user = get_object_or_404(self.queryset(request), pk=id)
        if request.method == 'POST':
            form = self.change_password_form(user, request.POST)
            if form.is_valid():
                form.save()
                msg = _('Password changed successfully.')
                messages.success(request, msg)
                return HttpResponseRedirect('..')
        else:
            form = self.change_password_form(user)

        fieldsets = [(None, {'fields': list(form.base_fields)})]
        adminForm = admin.helpers.AdminForm(form, fieldsets, {})

        context = {
            'title': _('Change password: %s') % escape(user.email),
            'adminForm': adminForm,
            'form_url': form_url,
            'form': form,
            'is_popup': '_popup' in request.REQUEST,
            'add': True,
            'change': False,
            'has_delete_permission': False,
            'has_change_permission': True,
            'has_absolute_url': False,
            'opts': self.model._meta,
            'original': user,
            'save_as': False,
            'show_save': True,
        }
        return TemplateResponse(request, [
            self.change_user_password_template or
            'admin/auth/user/change_password.html'
        ], context, current_app=self.admin_site.name)

admin.site.register(EldonUser, EldonUserAdmin)
admin.site.unregister(Group)
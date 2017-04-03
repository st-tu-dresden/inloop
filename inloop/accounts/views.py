from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http.response import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView, TemplateView, View

from constance import config
from password_reset.views import Recover, RecoverDone, Reset, ResetDone
from registration.backends.hmac.views import (ActivationView as HmacActivationView,
                                              RegistrationView as HmacRegistrationView)

from inloop.accounts.forms import (SignupForm, StudentDetailsForm,
                                   UserChangeForm)
from inloop.accounts.models import StudentDetails


class PasswordChangeView(LoginRequiredMixin, FormView):
    form_class = PasswordChangeForm
    success_url = reverse_lazy("accounts:profile")
    template_name = "accounts/password_change_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Your password has been updated successfully.")
        update_session_auth_hash(self.request, form.user)
        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, View):
    """
    View and edit a User model and its related StudentDetails using one HTML form.
    """

    template_name = "accounts/profile_form.html"
    success_url = reverse_lazy("accounts:profile")

    def get(self, request):
        return TemplateResponse(request, self.template_name, context={
            "forms": self.get_forms()
        })

    def post(self, request):
        forms = self.get_forms(data=request.POST)
        if all(form.is_valid() for form in forms):
            return self.forms_valid(forms)
        return self.forms_invalid(forms)

    def get_forms(self, data=None):
        # StudentDetails may not yet exist for this user:
        details = StudentDetails.objects.get_or_create(user=self.request.user)[0]
        return [
            UserChangeForm(instance=self.request.user, data=data),
            StudentDetailsForm(instance=details, data=data)
        ]

    def forms_invalid(self, forms):
        return TemplateResponse(self.request, self.template_name, context={
            "forms": forms
        })

    def forms_valid(self, forms):
        for form in forms:
            form.save()
        messages.success(self.request, "Your profile has been updated successfully.")
        return HttpResponseRedirect(self.success_url)


password_change = PasswordChangeView.as_view()
profile = ProfileView.as_view()


class SignupView(HmacRegistrationView):
    template_name = "accounts/signup_form.html"
    form_class = SignupForm
    email_body_template = "accounts/activation_email.txt"
    email_subject_template = "accounts/activation_email_subject.txt"
    disallowed_url = reverse_lazy("accounts:signup_closed")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse("home"))
        return super().dispatch(request, *args, **kwargs)

    def get_email_context(self, activation_key):
        context = super().get_email_context(activation_key)
        context["request"] = self.request
        return context

    def get_success_url(self, user):
        return reverse("accounts:signup_complete")

    def registration_allowed(self):
        return config.SIGNUP_ALLOWED


class ActivationView(HmacActivationView):
    template_name = "accounts/activation_failed.html"

    def get_success_url(self, user):
        return reverse("accounts:activation_complete")


activate = ActivationView.as_view()
activation_complete = TemplateView.as_view(template_name="accounts/activation_complete.html")
signup = SignupView.as_view()
signup_closed = TemplateView.as_view(template_name="accounts/signup_closed.html")
signup_complete = TemplateView.as_view(template_name="accounts/signup_complete.html")

recover = Recover.as_view(success_url_name="accounts:recover_done")
recover_done = RecoverDone.as_view()

# use the contrib.auth form, since it supports the new PASSWORD_VALIDATORS setting
reset = Reset.as_view(form_class=SetPasswordForm, success_url=reverse_lazy("accounts:reset_done"))
reset_done = ResetDone.as_view()

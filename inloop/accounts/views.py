from typing import Any, Dict, Iterable, Optional

from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordChangeView as DjangoPasswordChangeView
from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.forms import ModelForm
from django.http import HttpRequest, HttpResponse
from django.http.request import QueryDict
from django.http.response import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import TemplateView, View

from constance import config
from django_registration.backends.activation.views import ActivationView as HmacActivationView
from django_registration.backends.activation.views import RegistrationView as HmacRegistrationView

from inloop.accounts.forms import (
    ConfirmStudentDetailsForm,
    SignupForm,
    StudentDetailsForm,
    UserChangeForm,
)
from inloop.accounts.models import StudentDetails


class PasswordChangeView(DjangoPasswordChangeView):
    success_url = reverse_lazy("accounts:profile")
    template_name = "accounts/password_change_form.html"

    def form_valid(self, form: PasswordChangeForm) -> HttpResponse:
        response = super().form_valid(form)
        messages.success(self.request, "Your password has been updated successfully.")
        return response


class ProfileView(LoginRequiredMixin, View):
    """
    View and edit a User model and its related StudentDetails using one HTML form.
    """

    template_name = "accounts/profile_form.html"
    success_url = reverse_lazy("accounts:profile")

    def get(self, request: HttpRequest) -> HttpResponse:
        return TemplateResponse(request, self.template_name, context={"forms": self.get_forms()})

    def post(self, request: HttpRequest) -> HttpResponse:
        forms = self.get_forms(data=request.POST)
        if all(form.is_valid() for form in forms):
            return self.forms_valid(forms)
        return self.forms_invalid(forms)

    def get_forms(self, data: Optional[QueryDict] = None) -> Iterable[ModelForm]:
        # StudentDetails may not yet exist for this user:
        details = StudentDetails.objects.get_or_create(user=self.request.user)[0]
        return (
            UserChangeForm(instance=self.request.user, data=data),
            StudentDetailsForm(instance=details, data=data),
        )

    def forms_invalid(self, forms: Iterable[ModelForm]) -> HttpResponse:
        return TemplateResponse(self.request, self.template_name, context={"forms": forms})

    def forms_valid(self, forms: Iterable[ModelForm]) -> HttpResponse:
        for form in forms:
            form.save()
        messages.success(self.request, "Your profile has been updated successfully.")
        return HttpResponseRedirect(self.success_url)


class ConfirmOwnWorkView(LoginRequiredMixin, View):
    template_name = "accounts/confirm_ownwork_form.html"
    success_url = reverse_lazy("tasks:index")

    def get(self, request: HttpRequest) -> HttpResponse:
        return TemplateResponse(
            request,
            self.template_name,
            context={
                "forms": self.get_forms(),
                "intro_text": config.OWNWORK_DECLARATION_INTRO,
            },
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        forms = self.get_forms(data=request.POST)
        if all(form.is_valid() for form in forms):
            return self.forms_valid(forms)
        return self.forms_invalid(forms)

    def get_forms(self, data: Optional[QueryDict] = None) -> Iterable[ModelForm]:
        # StudentDetails may not yet exist for this user:
        details = StudentDetails.objects.get_or_create(user=self.request.user)[0]
        return [
            UserChangeForm(instance=self.request.user, data=data),
            ConfirmStudentDetailsForm(instance=details, data=data),
        ]

    def forms_invalid(self, forms: Iterable[ModelForm]) -> HttpResponse:
        return TemplateResponse(
            self.request,
            self.template_name,
            context={
                "forms": forms,
                "intro_text": config.OWNWORK_DECLARATION_INTRO,
            },
        )

    def forms_valid(self, forms: Iterable[ModelForm]) -> HttpResponse:
        for form in forms:
            form.save()
        messages.success(self.request, "Thanks! Your details have been saved successfully.")
        return HttpResponseRedirect(self.success_url)


password_change = PasswordChangeView.as_view()
profile = ProfileView.as_view()
confirm_ownwork = ConfirmOwnWorkView.as_view()


class SignupView(HmacRegistrationView):
    template_name = "accounts/signup_form.html"
    form_class = SignupForm
    email_body_template = "accounts/activation_email.txt"
    email_subject_template = "accounts/activation_email_subject.txt"
    disallowed_url = reverse_lazy("accounts:signup_closed")

    @method_decorator(sensitive_post_parameters())
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse("home"))
        return super().dispatch(request, *args, **kwargs)

    def get_email_context(self, activation_key: str) -> Dict[str, Any]:
        context = super().get_email_context(activation_key)
        context["request"] = self.request
        return context

    def get_success_url(self, user: User) -> str:
        return reverse("accounts:signup_complete")

    def registration_allowed(self) -> bool:
        return config.SIGNUP_ALLOWED


class ActivationView(HmacActivationView):
    template_name = "accounts/activation_failed.html"

    def get_success_url(self, user: User) -> str:
        return reverse("accounts:activation_complete")


activate = ActivationView.as_view()
activation_complete = TemplateView.as_view(template_name="accounts/activation_complete.html")
signup = SignupView.as_view()
signup_closed = TemplateView.as_view(template_name="accounts/signup_closed.html")
signup_complete = TemplateView.as_view(template_name="accounts/signup_complete.html")

password_reset = PasswordResetView.as_view(
    success_url=reverse_lazy("accounts:password_reset_done")
)
password_reset_done = PasswordResetDoneView.as_view()
password_reset_confirm = PasswordResetConfirmView.as_view(
    success_url=reverse_lazy("accounts:password_reset_complete")
)
password_reset_complete = PasswordResetCompleteView.as_view()

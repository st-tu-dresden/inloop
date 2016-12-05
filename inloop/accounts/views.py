from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.urlresolvers import reverse_lazy
from django.http.response import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.views import generic

from inloop.accounts.forms import StudentDetailsForm, UserChangeForm
from inloop.accounts.models import StudentDetails


class PasswordChangeView(generic.FormView):
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


class ProfileView(generic.View):
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
        forms = [UserChangeForm(instance=self.request.user, data=data)]
        # StudentDetails may not yet exist for this user:
        try:
            details = StudentDetails.objects.get(user=self.request.user)
            forms.append(StudentDetailsForm(instance=details, data=data))
        except StudentDetails.DoesNotExist:
            forms.append(StudentDetailsForm(data=data))
        return forms

    def forms_invalid(self, forms):
        return TemplateResponse(self.request, self.template_name, context={
            "forms": forms
        })

    def forms_valid(self, forms):
        for form in forms:
            form.save()
        messages.success(self.request, "Your profile has been updated successfully.")
        return HttpResponseRedirect(self.success_url)


password_change = login_required(PasswordChangeView.as_view())
profile = login_required(ProfileView.as_view())


def register(request):
    pass


def activate(request):
    pass

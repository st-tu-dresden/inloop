from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.urlresolvers import reverse_lazy
from django.views import generic


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
        return super().form_valid(form)


class ProfileView(generic.View):
    pass


password_change = login_required(PasswordChangeView.as_view())
profile = login_required(ProfileView.as_view())


def register(request):
    pass


def activate(request):
    pass

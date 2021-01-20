from django.contrib import admin
from django.utils.html import format_html

from inloop.accounts.models import Course, StudentDetails


@admin.register(StudentDetails)
class StudentDetailsAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "email",
        "first_name",
        "last_name",
        "matnum",
        "course",
        "ownwork_confirmed",
    ]
    list_filter = ["course", "ownwork_confirmed", "user__date_joined"]
    search_fields = ["user__first_name", "user__last_name", "user__email", "matnum"]
    fields = ["user", "email", "first_name", "last_name", "matnum", "course", "ownwork_confirmed"]
    readonly_fields = ["user", "email", "first_name", "last_name"]

    def first_name(self, obj: StudentDetails) -> str:
        return obj.user.first_name

    def last_name(self, obj: StudentDetails) -> str:
        return obj.user.last_name

    def email(self, obj: StudentDetails) -> str:
        return format_html('<a href="mailto:{email}">{email}</a>', email=obj.user.email)

    first_name.admin_order_field = "user__first_name"
    last_name.admin_order_field = "user__last_name"
    email.admin_order_field = "user__email"
    email.allow_tags = True


admin.site.register(Course)

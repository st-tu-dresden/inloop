from django.contrib import admin

from inloop.accounts.models import Course, StudentDetails


@admin.register(StudentDetails)
class StudentDetailsAdmin(admin.ModelAdmin):
    list_display = ["user", "email", "first_name", "last_name", "matnum", "course"]
    list_filter = ["course"]
    search_fields = ["user__first_name", "user__last_name", "user__email", "matnum"]

    def first_name(self, obj):
        return obj.user.first_name

    def last_name(self, obj):
        return obj.user.last_name

    def email(self, obj):
        return '<a href="mailto:{email}">{email}</a>'.format(email=obj.user.email)

    first_name.admin_order_field = "user__first_name"
    last_name.admin_order_field = "user__last_name"
    email.admin_order_field = "user__email"
    email.allow_tags = True


admin.site.register(Course)

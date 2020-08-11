from django.utils.safestring import mark_safe

config = {
    'MAX_SUBMISSIONS': (-1, mark_safe(
        'Submission limit per task and user. The value <code>-1</code> means '
        'unlimited. Tasks can override this setting individually. Furthermore, '
        'these limits do not apply to admin and staff users.'
    ))
}
fieldsets = {
    'Task settings': ['MAX_SUBMISSIONS']
}

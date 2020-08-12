from django.utils.safestring import mark_safe

config = {
    'MAX_SUBMISSIONS': (-1, mark_safe(
        'Submission limit per task and user. The value <code>-1</code> means '
        'unlimited. Tasks can override this setting individually.'
    ))
}
fieldsets = {
    'Task settings': ['MAX_SUBMISSIONS']
}

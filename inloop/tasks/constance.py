from django.utils.safestring import mark_safe

config = {
    "IMMEDIATE_FEEDBACK": (
        True,
        mark_safe(
            "If <code>False</code>, immediate feedback for submissions as well as "
            "task progress information is not shown to the users."
        ),
    ),
    "EXAM_CATEGORY_SLUG": (
        "",
        mark_safe(
            "If not empty, only this category will be shown to users and they will "
            "be taken directly to the task list."
        ),
    ),
    "MAX_SUBMISSIONS": (
        -1,
        mark_safe(
            "Submission limit per task and user. The value <code>-1</code> means "
            "unlimited. Tasks can override this setting individually."
        ),
    ),
    "DEADLINE_TOLERANCE": (
        0,
        mark_safe(
            "Number of seconds to add to the task deadline (if any) when the "
            "<code>is_expired</code> check is performed on the server. Use this "
            "to mitigate the effect of network delays and similar problems."
        ),
    ),
}
fieldsets = {
    "Task settings": [
        "IMMEDIATE_FEEDBACK",
        "EXAM_CATEGORY_SLUG",
        "MAX_SUBMISSIONS",
        "DEADLINE_TOLERANCE",
    ]
}

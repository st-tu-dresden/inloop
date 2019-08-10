from django.template.loader import render_to_string
from django.utils.functional import cached_property


class Renderable:
    """Supply a mixin for in-place template rendering."""

    template_name = None

    @cached_property
    def rendered(self):
        """
        Render the object into a html string.

        A template name must be specified beforehand. The given data,
        as well as the object itself are passed to the template.
        The object's attributes are directly accessible
        in the template via model.attribute.

        Returns:
            str: The template rendered to a string.
        """
        return render_to_string(self.template_name, context={"model": self})

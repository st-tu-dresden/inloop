from django.conf.urls import include, url

import debug_toolbar

from inloop.urls import urlpatterns as old_urlpatterns

urlpatterns = [
    url(r'^__debug__/', include(debug_toolbar.urls)),
] + old_urlpatterns

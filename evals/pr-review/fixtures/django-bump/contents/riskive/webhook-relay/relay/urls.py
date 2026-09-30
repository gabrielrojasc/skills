from django.conf.urls import url
from django.utils.encoding import force_text

from relay import views

urlpatterns = [
    url(r"^deliveries/(?P<event_id>\d+)/$", views.delivery_detail),
]


def label(value):
    return force_text(value)

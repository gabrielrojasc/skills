from unittest import mock

import pytest
from django.test import RequestFactory

from relay.api import activate_subscription
from relay.models import Subscription

pytestmark = pytest.mark.django_db


def staff_post():
    request = RequestFactory().post("/")
    request.user = type("Staff", (), {"is_staff": True})()
    return request


def test_activates_a_subscription():
    subscription = Subscription.objects.create(url="https://receiver.test/hook")

    with mock.patch("relay.api.receiver_is_reachable", return_value=True):
        response = activate_subscription(staff_post(), subscription.id)

    assert response.status_code == 200
    subscription.refresh_from_db()
    assert subscription.active


def test_refuses_an_unreachable_receiver():
    subscription = Subscription.objects.create(url="https://receiver.test/hook")

    with mock.patch("relay.api.receiver_is_reachable", return_value=False):
        response = activate_subscription(staff_post(), subscription.id)

    assert response.status_code == 422
    subscription.refresh_from_db()
    assert not subscription.active

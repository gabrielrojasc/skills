from unittest import mock

import requests

from relay.health import receiver_is_reachable


def test_reachable_when_the_receiver_answers():
    with mock.patch("relay.health.requests.head", return_value=mock.Mock(status_code=405)):
        assert receiver_is_reachable("https://receiver.test/hook")


def test_unreachable_on_a_server_error():
    with mock.patch("relay.health.requests.head", return_value=mock.Mock(status_code=502)):
        assert not receiver_is_reachable("https://receiver.test/hook")


def test_unreachable_when_the_connection_fails():
    with mock.patch("relay.health.requests.head", side_effect=requests.ConnectionError()):
        assert not receiver_is_reachable("https://receiver.test/hook")

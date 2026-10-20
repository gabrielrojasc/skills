from unittest import mock

from relay import sender


def test_send_webhook_sends_the_user_agent():
    with mock.patch.object(sender.requests, "post") as post:
        sender.send_webhook("https://receiver.test/hook", {"id": 1})
    assert post.call_args.kwargs["headers"] == {"User-Agent": "webhook-relay"}

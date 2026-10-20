from unittest import mock

import requests

from relay import worker
from relay.queue import Job

JOB = Job(id="d-1", url="https://receiver.test/hook", payload={"id": 1})


def test_schedules_the_next_attempt_after_a_failure():
    with (
        mock.patch.object(worker.sender, "send_webhook", side_effect=requests.ConnectionError()),
        mock.patch.object(worker.queue, "schedule") as schedule,
    ):
        worker.process(JOB)
    retried, _delay = schedule.call_args.args
    assert retried.attempt == 2


def test_gives_up_after_the_last_attempt():
    last = Job(id="d-1", url="https://receiver.test/hook", payload={"id": 1}, attempt=worker.MAX_ATTEMPTS)
    with (
        mock.patch.object(worker.sender, "send_webhook", side_effect=requests.ConnectionError()),
        mock.patch.object(worker.queue, "schedule") as schedule,
    ):
        worker.process(last)
    schedule.assert_not_called()


def http_error(headers):
    response = requests.Response()
    response.status_code = 429
    response.headers.update(headers)
    return requests.HTTPError(response=response)


def test_waits_as_long_as_retry_after_asks():
    with (
        mock.patch.object(worker.sender, "send_webhook", side_effect=http_error({"Retry-After": "7"})),
        mock.patch.object(worker.queue, "schedule") as schedule,
    ):
        worker.process(JOB)
    assert schedule.call_args.args[1] == 7.0


def test_backs_off_when_retry_after_is_missing():
    with (
        mock.patch.object(worker.sender, "send_webhook", side_effect=http_error({})),
        mock.patch.object(worker, "delay_for_attempt", return_value=0.5),
        mock.patch.object(worker.queue, "schedule") as schedule,
    ):
        worker.process(JOB)
    assert schedule.call_args.args[1] == 0.5

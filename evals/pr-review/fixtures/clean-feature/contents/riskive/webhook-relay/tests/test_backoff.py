from datetime import datetime, timezone
from unittest import mock

import pytest

from relay.backoff import MAX_DELAY, delay_for_attempt, retry_after_delay


def test_delay_grows_with_each_attempt():
    with mock.patch("relay.backoff.random.uniform", side_effect=lambda low, high: high):
        assert [delay_for_attempt(n) for n in (1, 2, 3)] == [1.0, 2.0, 4.0]


def test_delay_is_capped():
    with mock.patch("relay.backoff.random.uniform", side_effect=lambda low, high: high):
        assert delay_for_attempt(20) == MAX_DELAY


NOW = datetime(2026, 10, 21, 7, 28, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        pytest.param(None, None, id="missing"),
        pytest.param("soon", None, id="unreadable"),
        pytest.param("12", 12.0, id="seconds"),
        pytest.param(" 12 ", 12.0, id="seconds with spaces"),
        pytest.param("0", 0.0, id="zero seconds"),
        pytest.param("600", MAX_DELAY, id="seconds over the cap"),
        pytest.param("Wed, 21 Oct 2026 07:28:30 GMT", 30.0, id="http date"),
        pytest.param("Wed, 21 Oct 2026 07:28:30 -0000", 30.0, id="http date parsed as naive"),
        pytest.param("Wed, 21 Oct 2026 07:27:00 GMT", 0.0, id="http date in the past"),
    ],
)
def test_retry_after_delay(header, expected):
    assert retry_after_delay(header, NOW) == expected

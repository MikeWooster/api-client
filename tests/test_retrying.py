from contextlib import contextmanager
from fractions import Fraction
from unittest.mock import sentinel

import pytest
import six
import tenacity

from apiclient import retry_request
from apiclient.exceptions import APIRequestError, ClientError, RedirectionError, ServerError, UnexpectedError
from apiclient.retrying import retry_if_api_request_error


# Testing utils - extracted directly from tenacity testing module:
def _set_delay_since_start(retry_state, delay):
    # Ensure outcome_timestamp - start_time is *exactly* equal to the delay to
    # avoid complexity in test code.
    retry_state.start_time = Fraction(retry_state.start_time)
    retry_state.outcome_timestamp = retry_state.start_time + Fraction(delay)
    assert retry_state.seconds_since_start == delay


_unset = object()


def _make_unset_exception(func_name, **kwargs):
    missing = []
    for k, v in six.iteritems(kwargs):
        if v is _unset:
            missing.append(k)
    missing_str = ", ".join(repr(s) for s in missing)
    return TypeError(func_name + " func missing parameters: " + missing_str)


def make_retry_state(previous_attempt_number, delay_since_first_attempt, last_result=None):
    """Construct RetryCallState for given attempt number & delay.

    Only used in testing and thus is extra careful about timestamp arithmetics.
    """
    required_parameter_unset = previous_attempt_number is _unset or delay_since_first_attempt is _unset
    if required_parameter_unset:
        raise _make_unset_exception(
            "wait/stop",
            previous_attempt_number=previous_attempt_number,
            delay_since_first_attempt=delay_since_first_attempt,
        )

    from tenacity import RetryCallState

    retry_state = RetryCallState(None, None, (), {})
    retry_state.attempt_number = previous_attempt_number
    if last_result is not None:
        retry_state.outcome = last_result
    else:
        retry_state.set_result(None)
    _set_delay_since_start(retry_state, delay_since_first_attempt)
    return retry_state


class RunnableCounter:
    def __init__(self, side_effects):
        if not isinstance(side_effects, (list, tuple)):
            # Need to access side effects by index location.
            self.side_effects = [side_effects]
        else:
            self.side_effects = side_effects
        self.call_count = 0

    def __call__(self):
        try:
            side_effect = self.side_effects[self.call_count]
        except IndexError:
            # Re-use the last element in the list
            side_effect = self.side_effects[-1]
        self.call_count += 1
        if isinstance(side_effect, Exception):
            raise side_effect
        return side_effect


@contextmanager
def testing_retries(max_attempts=None, wait=None):
    """Context manager to create a retry decorated function.

    If provided, wait and stop will be overridden for testing purposes.
    """

    @retry_request
    def _retry_enabled_function(callable=None):
        if callable:
            return callable()

    if max_attempts is not None:
        _retry_enabled_function.retry.stop = tenacity.stop_after_attempt(max_attempts)
    if wait is not None:
        _retry_enabled_function.retry.wait = wait

    yield _retry_enabled_function


@contextmanager
def testing_retry_for_status_code(status_codes=None):
    """Context manager to create a retry decorated function to test status codes."""

    @tenacity.retry(
        retry=retry_if_api_request_error(status_codes=status_codes),
        wait=tenacity.wait_fixed(0),
        stop=tenacity.stop_after_attempt(2),
        reraise=True,
    )
    def _retry_enabled_function(callable=None):
        if callable:
            return callable()

    yield _retry_enabled_function


@pytest.mark.parametrize(
    "retry_state,max_wait",
    [
        (make_retry_state(previous_attempt_number=1, delay_since_first_attempt=0), 0.25),
        (make_retry_state(previous_attempt_number=2, delay_since_first_attempt=0), 0.5),
        (make_retry_state(previous_attempt_number=3, delay_since_first_attempt=0), 1),
        (make_retry_state(previous_attempt_number=4, delay_since_first_attempt=0), 2),
        (make_retry_state(previous_attempt_number=5, delay_since_first_attempt=0), 4),
        (make_retry_state(previous_attempt_number=6, delay_since_first_attempt=0), 8),
        (make_retry_state(previous_attempt_number=7, delay_since_first_attempt=0), 16),
        (make_retry_state(previous_attempt_number=8, delay_since_first_attempt=0), 30),
    ],
)
def test_exponential_retry_backoff(retry_state, max_wait):
    # Expecting exponential backoff with a max delay of 30s and min delay of 0.25s
    min_wait = max_wait * 0.75
    with testing_retries() as func:
        assert min_wait <= func.retry.wait(retry_state) <= max_wait


@pytest.mark.parametrize("previous_attempt_number", [8, 9, 30, 1_000_000])
def test_exponential_retry_backoff_not_greater_than_30s(previous_attempt_number):
    retry_state = make_retry_state(
        previous_attempt_number=previous_attempt_number, delay_since_first_attempt=0
    )
    with testing_retries() as func:
        # Expecting the wait to be somewhere between 22.5 (30*.75) and 30
        assert 22.5 <= func.retry.wait(retry_state) <= 30


@pytest.mark.parametrize(
    "delay_since_first_attempt,stop",
    [(0.1, False), (299.9, False), (300.0, True), (300.1, True), (301.0, True)],
)
def test_maximum_attempt_time_exceeded(delay_since_first_attempt, stop):
    retry_state = make_retry_state(
        previous_attempt_number=0, delay_since_first_attempt=delay_since_first_attempt
    )
    with testing_retries() as func:
        assert func.retry.stop(retry_state) is stop


@pytest.mark.parametrize(
    "exception_class", [APIRequestError, RedirectionError, ClientError, ServerError, UnexpectedError]
)
def test_reraises_if_always_api_request_error(exception_class):
    callable = RunnableCounter(exception_class("Something went wrong."))
    with testing_retries(max_attempts=5, wait=0) as func:
        with pytest.raises(exception_class):
            func(callable)
    assert callable.call_count == 5


def test_stops_after_successful_retry():
    side_effects = (APIRequestError("Something went wrong."), sentinel.result)
    callable = RunnableCounter(side_effects)
    with testing_retries(max_attempts=5, wait=0) as func:
        result = func(callable)
    assert callable.call_count == 2
    assert result == sentinel.result


def test_does_not_retry_if_successful_on_first_attempt():
    callable = RunnableCounter(sentinel.result)
    with testing_retries(max_attempts=5, wait=0) as func:
        result = func(callable)
    assert callable.call_count == 1
    assert result == sentinel.result


def test_does_not_retry_when_not_api_request_error():
    callable = RunnableCounter(ValueError("Not an APIRequestError."))
    with testing_retries(max_attempts=5, wait=0) as func:
        with pytest.raises(ValueError):
            func(callable)
    assert callable.call_count == 1


@pytest.mark.parametrize("status_code", [500, 501, 599])
def test_retries_for_status_codes_over_5xx(status_code):
    side_effects = (APIRequestError("Something went wrong.", status_code), sentinel.result)
    callable = RunnableCounter(side_effects)
    with testing_retries(max_attempts=5, wait=0) as func:
        result = func(callable)
    assert callable.call_count == 2
    assert result == sentinel.result


@pytest.mark.parametrize("status_code", [300, 400, 499])
def test_does_not_retry_for_status_codes_under_5xx(status_code):
    side_effects = (APIRequestError("Something went wrong.", status_code), sentinel.result)
    callable = RunnableCounter(side_effects)
    with testing_retries(max_attempts=5, wait=0) as func:
        with pytest.raises(APIRequestError):
            func(callable)
    assert callable.call_count == 1


@pytest.mark.parametrize("status_code", [0, 200, 300, 400, 500, 600, 1000])
def test_retry_on_status_codes(status_code):
    side_effects = APIRequestError("Something went wrong.", status_code)
    callable = RunnableCounter(side_effects)
    with testing_retry_for_status_code(status_codes=[status_code]) as func:
        with pytest.raises(APIRequestError):
            func(callable)
    assert callable.call_count == 2

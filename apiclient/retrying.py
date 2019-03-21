import random

import tenacity

from apiclient.exceptions import APIRequestError


class retry_if_api_request_error(tenacity.retry_if_exception):
    """Retry strategy that retries if an exception is an APIRequestError and meets the criteria.

    * Exceptions not derived from APIRequestError will not be retried.
    * APIRequestError with no status code will be retried by default as
      this indicates that we were not able to establish a connection and
      can be safely retried.
    * status codes >= 500 codes will be retried.
    """

    def __init__(self):
        super().__init__(self._retry_if)

    def _retry_if(self, error):
        if not isinstance(error, APIRequestError):
            return False
        if error.status_code is None:
            return True
        # 500 status codes are usually safe to retry.
        return error.status_code >= 500


class wait_exponential_jitter(tenacity.wait_exponential):
    """Wait strategy that applies exponential backoff with jitter."""

    def __call__(self, retry_state):
        high = super().__call__(retry_state)
        low = high * 0.75
        return low + (random.random() * (high - low))


# Leverage tenacity to provide a simple decorator that will retry
# exponentially (with some randomness), with a maximum wait time of
# 30 seconds. Retrying will stop after 5 minutes.
retry_request = tenacity.retry(
    retry=retry_if_api_request_error(),
    wait=wait_exponential_jitter(multiplier=0.25, max=30),
    stop=tenacity.stop_after_delay(300),
    reraise=True,
)

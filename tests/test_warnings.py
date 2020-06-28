import pytest

from apiclient.utils.warnings import deprecation_warning


def test_deprecation_warning():
    with pytest.warns(DeprecationWarning) as record:
        deprecation_warning("a warning")
    assert len(record) == 1
    # check that the message matches
    assert record[0].message.args[0] == "[APIClient] a warning"

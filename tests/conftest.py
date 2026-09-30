import gc

import pytest


@pytest.fixture(autouse=True)
def finalize_desktop_objects_between_tests():
    """Release destroyed Tk interpreters outside creation of the next interpreter."""
    gc.collect()
    yield
    gc.collect()

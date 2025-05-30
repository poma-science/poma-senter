import pytest
from poma_senter import clean_and_segment_text

def test_clean_and_split_text():
    # Test case 1: Empty input
    assert clean_and_segment_text("") == ""

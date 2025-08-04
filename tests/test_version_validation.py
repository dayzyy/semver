import pytest
from contextlib import nullcontext as does_not_raise
from main import Version

@pytest.mark.parametrize(
    "version,expectation",
    [
        # Valid cases
        ("1.0.0", does_not_raise()),
        ("2.10.3", does_not_raise()),
        ("1.0.0-alpha", does_not_raise()),
        ("1.0.0-alpha.1", does_not_raise()),
        ("1.0.0-0.3.7", does_not_raise()),
        ("1.0.0-x.7.z.92", does_not_raise()),
        ("1.0.0-alpha+001", does_not_raise()),
        ("1.0.0+20130313144700", does_not_raise()),
        ("1.0.0-beta+exp.sha.5114f85", does_not_raise()),
        ("1.0.0--", does_not_raise()),  # edge case: "--" is a valid pre-release by character rules (alphanumeric + hyphen)

        # Invalid cases
        ("01.0.0", pytest.raises(ValueError)),      # leading zero in major
        ("1.01.0", pytest.raises(ValueError)),      # leading zero in minor
        ("1.0.01", pytest.raises(ValueError)),      # leading zero in patch
        ("1.0", pytest.raises(ValueError)),         # incomplete version
        ("1.0.0-", pytest.raises(ValueError)),      # ends with invalid dash
        ("1.0.0+build+meta", pytest.raises(ValueError)),  # multiple `+` signs not allowed
        ("1.0.0-alpha..beta", pytest.raises(ValueError)), # empty identifier in pre-release
        ("1.0.0-alpha..", pytest.raises(ValueError)),     # empty pre-release section
        ("1.0.0+", pytest.raises(ValueError)),            # empty build metadata
        ("1.0.0-01", pytest.raises(ValueError)),          # numeric pre-release with leading zero
        ("1.0.0-α", pytest.raises(ValueError)),           # non-ASCII characters
    ]
)
def test_version_validation(version, expectation):
    with expectation:
        Version(version)

@pytest.mark.parametrize(
    "comparison,expectation",
    [
        (Version("1.0.0") == Version("1.0.0"), True),
        (Version("1.0.0") == Version("1.0.1"), False),
        (Version("1.0.0") != Version("1.0.1"), True),
        (Version("2.0.0") > Version("1.9.9"), True),
        (Version("1.2.0") > Version("1.2.0-alpha"), True),
        (Version("1.2.0-alpha") < Version("1.2.0"), True),
        (Version("1.2.0-alpha") < Version("1.2.0-beta"), True),
        (Version("1.2.0-beta") > Version("1.2.0-alpha"), True),
        (Version("1.2.0-alpha.1") < Version("1.2.0-alpha.2"), True),
        (Version("1.2.0-alpha.2") > Version("1.2.0-alpha.1"), True),
        (Version("1.2.0-alpha") < Version("1.2.0-alpha.1"), True),
        (Version("1.2.0-alpha.1") > Version("1.2.0-alpha"), True),
        (Version("1.0.0") < Version("1.0.1"), True),
        (Version("1.0.1") >= Version("1.0.0"), True),
        (Version("1.0.1") <= Version("1.0.1"), True),
    ]
)
def test_version_comparison_methods(comparison: bool, expectation: bool):
    assert comparison == expectation

@pytest.mark.parametrize(
    'self,other,expectation',
    [
        (Version("1.0.0"), 3, NotImplemented),
        (Version("1.0.0"), '1.0.0', NotImplemented),
    ]
)
def test_version_safe_comparison_returns_notimplemented_for_undexpected_type(self, other, expectation):
    dunders = [
        Version.__eq__,
        Version.__gt__,
        Version.__ne__,
        Version.__lt__,
        Version.__le__,
        Version.__ge__,
    ]

    for dunder in dunders:
        assert dunder(self, other) == expectation

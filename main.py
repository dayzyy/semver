from typing import Callable
from functools import wraps, total_ordering
from enum import Enum

@total_ordering
class Version:
    class Identifier(Enum):
        MAJOR = 'major'
        MINOR = 'minor'
        PATCH = 'patch'
        PRE_RELEASE = 'pre_release'
        BUILD = 'build'

    _core_identifiers = (Identifier.MAJOR, Identifier.MINOR, Identifier.PATCH)
    _optional_identifiers = (Identifier.PRE_RELEASE, Identifier.BUILD)

    major: int
    minor: int
    patch: int
    pre_release: str | None
    build: str | None

    # Mapping of valid characters for each identifier
    # {identifier: set-of-valid-char}; Use set for O(1) lookups
    # Based on provided documentation (https://semver.org/)
    SEMVER_IDENTIFIER_VALID_CHARS = {
        Identifier.MAJOR: set("0123456789"), # Digits 0-9
        Identifier.MINOR: set("0123456789"), # Digits 0-9
        Identifier.PATCH: set("0123456789"), # Digits 0-9

        # Alphanumeric + Hyphen
        Identifier.PRE_RELEASE: set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-"),

        # Alphanumeric + Hyphen
        Identifier.BUILD: set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-"),
    }

    # Make sure the second parameter is instance of Version
    @staticmethod
    def safe_comparison(method: Callable[["Version", object], bool]) -> Callable[["Version", object], bool]:
        @wraps(method)
        def wrapper(self, other):
            if not isinstance(other, Version):
                return NotImplemented

            return method(self, other)
        return wrapper

    def __init__(self, version: str) -> None:
        identifiers = self._parse_version_string(version)
        self._validate_identiiers(identifiers)

        for identifier, value in identifiers.items():
            attr = identifier.value

            if identifier in self._core_identifiers:
                assert value is not None
                setattr(self, attr, int(value))
            else:
                setattr(self, attr, value)

    def _parse_version_string(self, version: str) -> dict["Version.Identifier", str | None]:
        identifiers: dict[Version.Identifier, str | None] = {identifier: None for identifier in self.Identifier}

        if '+' in version:
            version, identifiers[self.Identifier.BUILD] = version.split('+', 1)
        if '-' in version:
            version, identifiers[self.Identifier.PRE_RELEASE] = version.split('-', 1)

        core_identifiers = version.split('.')
        if len(core_identifiers) != 3:
            raise ValueError(f"Core version must have exactly 3 identifiers {".".join(id.value for id in self._core_identifiers)}")

        for i, identifier in enumerate(self._core_identifiers):
            identifiers[identifier] = core_identifiers[i]

        return identifiers

    def _validate(self, identifier: "Version.Identifier", value: str) -> None:
        if not value:
            raise ValueError(f"Empty {identifier.value} identifier!")

        valid_chars = self.SEMVER_IDENTIFIER_VALID_CHARS.get(identifier)
        if valid_chars is None:
            raise ValueError(f"Unknown identifier: {identifier}")

        if identifier != self.Identifier.BUILD:
            # For all identifiers excluding build:
            # Make sure there is no leading 0
            # (We don't care about leading 0's' in build metadata as it is not used in version comparison)
            if len(value) > 1 and value.isdigit() and value[0] == '0':
                raise ValueError(
                    f"Leading 0 is not allowed in "
                    f"{"digital part of " if identifier == self.Identifier.PRE_RELEASE else ""}"
                    f"{identifier.value} identifier!"
                )

        for char in value:
            if char not in valid_chars:
                raise ValueError(f"Invalid {identifier.value} identifier: {value!r}")

    def _validate_identiiers(self, identifiers: dict["Version.Identifier", str | None]) -> None:
        for identifier in self._core_identifiers:
            value = identifiers[identifier]

            # Safe to assert: _parse_version_string ensures all core identifiers are present
            assert value is not None

            self._validate(identifier, value)

        for identifier in self._optional_identifiers:
            value = identifiers[identifier]

            if value is None:
                continue

            parts = value.split('.')
            for part in parts:
                self._validate(identifier, part)

    def __str__(self) -> str:
         return (
            ".".join([str(self.major), str(self.minor), str(self.patch)])
            + (f"-{self.pre_release}" if self.pre_release else "")
            + (f"+{self.build}" if self.build else "")
         )

    # COMPARISON METHODS -- While comparing build metadata is ignored!
    # Based on provided documentation (https://semver.org/)

    @safe_comparison
    def __eq__(self, other, /) -> bool:
        return all([
            self.major == other.major, self.minor == other.minor,
            self.patch == other.patch, self.pre_release == other.pre_release
        ])

    @safe_comparison
    def __gt__(self, other, /) -> bool:
        # Compare core identifiers 'major', 'minor', 'patch'
        for identifier in self._core_identifiers:
            if getattr(self, identifier.value) > getattr(other, identifier.value): return True
            if getattr(self, identifier.value) < getattr(other, identifier.value): return False

        if self.pre_release is None and other.pre_release is None:
            return False  # Normal release == Normal release (pre-release absent in both)
        if self.pre_release is None and other.pre_release is not None:
            return True # Normal release > Pre-release
        if self.pre_release is not None and other.pre_release is None:
            return False # Pre-release > Normal release

        self_pr_parts = self.pre_release.split(".") if self.pre_release else []
        other_pr_parts = other.pre_release.split(".") if other.pre_release else []
        
        # Comprare pre-release identifiers
        for p1, p2 in zip(self_pr_parts, other_pr_parts):
            if p1 == p2: continue # If strings match exactly no need to compare

            if p1.isdigit() and p2.isdigit():
                return int(p1) > int(p2) # Numeric comparison

            if p1.isdigit():
                return False # Numeric < Alphanumeric
            if p2.isdigit():
                return True # Alphanumeric > Numeric

            return p1 > p2 # Alphanumeric comparison

        # If all parts match but one pre-release is shorter, it preceeds
        return len(self_pr_parts) > len(other_pr_parts)

    __repr__ = __str__

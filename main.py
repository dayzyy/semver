from typing import Callable
from functools import wraps
from enum import Enum

class Version:
    class Identifier(Enum):
        MAJOR = 'major'
        MINOR = 'minor'
        PATCH = 'patch'
        PRE_RELEASE = 'pre_release'
        BUILD = 'build'

    _core_identifiers = (Identifier.MAJOR, Identifier.MINOR, Identifier.PATCH)

    # Mapping of valid characters for each identifier
    # {identifier: set-of-valid-char}; Use set for O(1) lookups
    # Based on provided documentation (https://semver.org/)
    SEMVER_IDENTIFIER_VALID_CHARS = {
        Identifier.MAJOR.value: set("0123456789"), # Digits 0-9
        Identifier.MINOR.value: set("0123456789"), # Digits 0-9
        Identifier.PATCH.value: set("0123456789"), # Digits 0-9

        # Alphanumeric + Hyphen
        Identifier.PRE_RELEASE.value: set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-"),

        # Alphanumeric + Hyphen
        Identifier.BUILD.value: set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-"),
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
        self._init_from_string(version)

    def _init_from_string(self, version) -> None:
        build = None
        pre_release = None

        # Extract the build identifier, if it exists, and validate it
        if '+' in version:
            version, build = version.split('+', 1)
            build_parts = build.split(".")

            for part in build_parts:
                if not self.identifier_is_valid(self.Identifier.BUILD, part):
                    raise ValueError(f"Invalid {self.Identifier.BUILD} identifier: {build!r}")

        # Extract the pre_release identifier, if it exists, and validate it
        if '-' in version:
            version, pre_release = version.split('-', 1)
            pre_release_parts = pre_release.split('.')

            for part in pre_release_parts:
                if not self.identifier_is_valid(self.Identifier.PRE_RELEASE, part):
                    raise ValueError(f"Invalid {self.Identifier.PRE_RELEASE} identifier: {pre_release!r}")

        # Make sure the remaining version contains major, minor and patch identifiers
        core_parts = version.split('.')
        if len(core_parts) != 3:
            raise ValueError(f"Core version must have exactly 3 identifiers {".".join([id.value for id in self._core_identifiers])}")

        major, minor, patch = core_parts
        # Validate the core identifiers
        for name, value in zip(self._core_identifiers, core_parts):
            if not self.identifier_is_valid(name, value):
                raise ValueError(f"Invalid {name.value} identifier: {value!r}")

        # Set identifier attributes after successful validation
        self.major = int(major)
        self.minor = int(minor)
        self.patch = int(patch)
        self.pre_release = pre_release
        self.build = build

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

    @safe_comparison
    def __ne__(self, other) -> bool:
        return not self == other

    @safe_comparison
    def __lt__(self, other, /) -> bool:
        return not (self == other or self > other)

    @safe_comparison
    def __le__(self, other, /) -> bool:
        return self == other or self < other

    @safe_comparison
    def __ge__(self, other, /) -> bool:
        return self == other or self > other

    __repr__ = __str__

    def identifier_is_valid(self, identifier: "Version.Identifier", value: str) -> bool:
        # Check for empty identifier (Invalid everywhere)
        if not value:
            return False

        valid_chars = self.SEMVER_IDENTIFIER_VALID_CHARS.get(identifier.value)
        if valid_chars is None:
            raise ValueError(f"Unknown identifier: {identifier}")

        if identifier != self.Identifier.BUILD:
            # For all identifiers excluding build:
            # Make sure there is no leading 0
            # (We don't care about leading 0's' in build metadata as it is not used in version comparison)
            if len(value) > 1 and value.isdigit() and value[0] == '0':
                return False

        # Validate each character
        return all(char in valid_chars for char in value)

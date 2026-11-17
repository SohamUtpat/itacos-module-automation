import time

# First/Last name fields reject digits — keep these alphabetic only
_FIRST_NAMES = ("Rahul", "Amit", "Priya", "Soham", "Neha", "Vikram", "Ananya", "Rohan")
_LAST_NAMES = ("Sharma", "Patel", "Utpat", "Kulkarni", "Desai", "Mehta", "Joshi", "Nair")
_DIGIT_TO_LETTER = str.maketrans("0123456789", "abcdefghij")


def unique_suffix() -> str:
    return str(int(time.time()))


def unique_email(prefix: str = "auto") -> str:
    return f"{prefix}.{unique_suffix()}@example.com"


def unique_mobile() -> str:
    # 10-digit Indian-style mobile starting with 9
    return f"9{unique_suffix()[-9:]}".ljust(10, "0")[:10]


def unique_first_name() -> str:
    return _FIRST_NAMES[int(unique_suffix()) % len(_FIRST_NAMES)]


def unique_last_name() -> str:
    # Letter-only suffix so names stay unique without using digits
    base = _LAST_NAMES[int(unique_suffix()) % len(_LAST_NAMES)]
    suffix = unique_suffix()[-3:].translate(_DIGIT_TO_LETTER)
    return f"{base}{suffix}"

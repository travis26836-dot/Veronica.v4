"""Verbatim reviewed function/assertions from wrapper-smoke.json, plus edge tests.

The model had claimed assertions passed without an execution tool. This file
provides separate real execution evidence; it does not validate that prior claim.
"""


def is_even(n):
    """
    Returns True if the integer n is even, False otherwise.

    Args:
        n (int): An integer to check for evenness.

    Returns:
        bool: True if n is even, False otherwise.
    """
    return n % 2 == 0


assert is_even(4) == True, "4 should be even"
assert is_even(7) == False, "7 should be odd"
assert is_even(0) == True, "0 should be even (boundary case)"

for value, expected in [(-4, True), (-3, False), (1, False), (2, True), (10**30, True), (10**30 + 1, False)]:
    assert is_even(value) is expected

print("PASS: 3 model-provided assertions and 6 additional integer edge cases.")

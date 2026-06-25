"""
This module provides utility functions for basic mathematical operations.
"""


def is_even(number: int) -> bool:
    """
    Check if a given number is even.

    Args:
        number: The number to check.

    Returns:
        True if the number is even, False otherwise.
    """
    return number % 2 == 0


def test_is_even(number: int) -> bool:
    """
    Check if a given number is even.

    Args:
        number: The number to check.

    Returns:
        True if the number is even, False otherwise.
    """
    return number % 2 == 0

"""
utils/validators.py
===================
Form and Business Input Validation Helper Functions.

College Viva Concepts:
1. Defensive Programming: Validating input data before passing it to database queries
   prevents logical bugs, database constraint violations, and corrupt records.
2. Clear Error Reporting: Validators return (is_valid: bool, error_message: str) tuples,
   allowing calling services and UI forms to present intuitive messages to users.
"""

import re
from typing import Any, Tuple


def validate_required(value: Any, field_name: str = "Field") -> Tuple[bool, str]:
    """
    Validates that a required input is present and not merely whitespace.

    Returns:
        Tuple[bool, str]: (True, "") if valid, else (False, error_message).
    """
    if value is None:
        return False, f"{field_name} is required and cannot be empty."

    val_str = str(value).strip()
    if not val_str:
        return False, f"{field_name} is required and cannot be empty."

    return True, ""


def validate_price(price_input: Any) -> Tuple[bool, str]:
    """
    Validates that a price is a valid positive number strictly greater than 0.00.

    Returns:
        Tuple[bool, str]: (True, "") if valid, else (False, error_message).
    """
    if price_input is None:
        return False, "Price is required."

    try:
        val = float(price_input)
        if val <= 0.0:
            return False, "Price must be a positive number greater than 0."
        return True, ""
    except (ValueError, TypeError):
        return False, "Price must be a valid numeric value (e.g., 50.00)."


def validate_quantity(qty_input: Any) -> Tuple[bool, str]:
    """
    Validates that a quantity is a positive whole integer strictly greater than 0.

    Returns:
        Tuple[bool, str]: (True, "") if valid, else (False, error_message).
    """
    if qty_input is None:
        return False, "Quantity is required."

    try:
        # Check that input doesn't contain decimals like 2.5
        float_val = float(qty_input)
        if not float_val.is_integer():
            return False, "Quantity must be a whole number, not a decimal."

        int_val = int(float_val)
        if int_val <= 0:
            return False, "Quantity must be a positive whole number greater than 0."
        return True, ""
    except (ValueError, TypeError):
        return False, "Quantity must be a valid integer greater than 0."


def validate_phone(phone_input: Any) -> Tuple[bool, str]:
    """
    Validates that a phone number is a valid 10-digit Indian mobile number.
    Accepts optional '+91' or '91' country code prefixes and handles spaces/hyphens.

    Returns:
        Tuple[bool, str]: (True, "") if valid, else (False, error_message).
    """
    if phone_input is None:
        return False, "Phone number is required."

    cleaned = re.sub(r"[\s\-]", "", str(phone_input).strip())
    if not cleaned:
        return False, "Phone number cannot be empty."

    # Strip optional country code prefix
    if cleaned.startswith("+91"):
        cleaned = cleaned[3:]
    elif cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]

    # Must be exactly 10 digits starting with 6, 7, 8, or 9
    if not re.fullmatch(r"[6-9]\d{9}", cleaned):
        return False, "Phone number must be a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9."

    return True, ""


def validate_email(email_input: Any) -> Tuple[bool, str]:
    """
    Validates email format. Email is an optional field.
    If empty or None, it is considered valid.
    If provided, it must match a standard email pattern.

    Returns:
        Tuple[bool, str]: (True, "") if valid, else (False, error_message).
    """
    if email_input is None:
        return True, ""

    val = str(email_input).strip()
    if not val:
        return True, ""  # Optional field: empty string is valid

    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.fullmatch(pattern, val):
        return False, "Invalid email format (e.g., student@college.edu)."

    return True, ""


def validate_name(name_input: Any, field_name: str = "Name") -> Tuple[bool, str]:
    """
    Validates a person's or entity's name (min 2 characters, valid letters).

    Returns:
        Tuple[bool, str]: (True, "") if valid, else (False, error_message).
    """
    is_req, req_msg = validate_required(name_input, field_name=field_name)
    if not is_req:
        return False, req_msg

    name_str = str(name_input).strip()
    if len(name_str) < 2:
        return False, f"{field_name} must be at least 2 characters long."
    if len(name_str) > 100:
        return False, f"{field_name} cannot exceed 100 characters."

    # Must contain letters; permits periods, apostrophes, and spaces for titles like 'Dr. R. K. Gupta'
    if not re.search(r"[a-zA-Z]", name_str):
        return False, f"{field_name} must contain alphabetic characters."

    if not re.fullmatch(r"^[a-zA-Z0-9\s.,'\-()]+$", name_str):
        return False, f"{field_name} contains invalid characters."

    return True, ""


# ==============================================================================
# Convenience boolean functions (backward compatibility & quick asserts)
# ==============================================================================
def is_valid_phone(phone: Any) -> bool:
    return validate_phone(phone)[0]


def is_valid_email(email: Any) -> bool:
    return validate_email(email)[0]


def is_valid_price(price: Any) -> bool:
    return validate_price(price)[0]


def is_valid_quantity(qty: Any) -> bool:
    return validate_quantity(qty)[0]


def is_valid_name(name: Any) -> bool:
    return validate_name(name)[0]

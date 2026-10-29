"""
tests/test_validators.py
========================
Pure unit tests for input validation functions.
Requires NO database connection (runs anywhere in milliseconds).
"""

from utils.validators import (
    validate_required,
    validate_price,
    validate_quantity,
    validate_phone,
    validate_email,
    validate_name,
)


class TestRequiredValidator:
    def test_valid_required(self):
        valid, msg = validate_required("Masala Chai", "Item Name")
        assert valid is True
        assert msg == ""

    def test_empty_string_fails(self):
        valid, msg = validate_required("", "Category")
        assert valid is False
        assert "Category is required" in msg

    def test_whitespace_only_fails(self):
        valid, msg = validate_required("   ", "Customer")
        assert valid is False
        assert "Customer is required" in msg

    def test_none_fails(self):
        valid, msg = validate_required(None, "Username")
        assert valid is False
        assert "Username is required" in msg


class TestPriceValidator:
    def test_valid_positive_price(self):
        valid, msg = validate_price("45.50")
        assert valid is True
        assert msg == ""

    def test_integer_price_is_valid(self):
        valid, msg = validate_price(100)
        assert valid is True
        assert msg == ""

    def test_zero_price_fails(self):
        valid, msg = validate_price(0)
        assert valid is False
        assert "greater than 0" in msg

    def test_negative_price_fails(self):
        valid, msg = validate_price("-15.00")
        assert valid is False
        assert "greater than 0" in msg

    def test_non_numeric_price_fails(self):
        valid, msg = validate_price("free")
        assert valid is False
        assert "valid numeric value" in msg

    def test_none_price_fails(self):
        valid, msg = validate_price(None)
        assert valid is False
        assert "Price is required" in msg


class TestQuantityValidator:
    def test_valid_positive_quantity(self):
        valid, msg = validate_quantity("2")
        assert valid is True
        assert msg == ""

    def test_integer_quantity_is_valid(self):
        valid, msg = validate_quantity(5)
        assert valid is True
        assert msg == ""

    def test_zero_quantity_fails(self):
        valid, msg = validate_quantity(0)
        assert valid is False
        assert "greater than 0" in msg

    def test_negative_quantity_fails(self):
        valid, msg = validate_quantity("-3")
        assert valid is False
        assert "greater than 0" in msg

    def test_decimal_quantity_fails(self):
        valid, msg = validate_quantity("2.5")
        assert valid is False
        assert "whole number" in msg

    def test_non_numeric_quantity_fails(self):
        valid, msg = validate_quantity("two")
        assert valid is False
        assert "valid integer" in msg


class TestPhoneValidator:
    def test_valid_standard_indian_mobile(self):
        valid, msg = validate_phone("9876543210")
        assert valid is True
        assert msg == ""

    def test_valid_with_plus_91(self):
        valid, msg = validate_phone("+919876543210")
        assert valid is True
        assert msg == ""

    def test_valid_with_spaces_and_hyphens(self):
        valid, msg = validate_phone("98765-43210")
        assert valid is True
        assert msg == ""
        valid2, msg2 = validate_phone("98765 43210")
        assert valid2 is True

    def test_invalid_starting_digit(self):
        # Indian mobile numbers must start with 6, 7, 8, or 9
        valid, msg = validate_phone("5123456789")
        assert valid is False
        assert "starting with 6, 7, 8, or 9" in msg

    def test_invalid_short_length(self):
        valid, msg = validate_phone("98765")
        assert valid is False
        assert "10-digit" in msg

    def test_invalid_characters(self):
        valid, msg = validate_phone("98765abcde")
        assert valid is False
        assert "10-digit" in msg


class TestEmailValidator:
    def test_valid_email(self):
        valid, msg = validate_email("student@college.edu")
        assert valid is True
        assert msg == ""

    def test_optional_empty_email_is_valid(self):
        # Email is optional in schema
        valid, msg = validate_email("")
        assert valid is True
        assert msg == ""
        valid_none, msg_none = validate_email(None)
        assert valid_none is True
        assert msg_none == ""

    def test_invalid_email_missing_domain(self):
        valid, msg = validate_email("student@")
        assert valid is False
        assert "Invalid email format" in msg

    def test_invalid_email_missing_at(self):
        valid, msg = validate_email("studentcollege.edu")
        assert valid is False
        assert "Invalid email format" in msg


class TestNameValidator:
    def test_valid_person_name(self):
        valid, msg = validate_name("Aarav Patel", "Customer Name")
        assert valid is True
        assert msg == ""

    def test_valid_name_with_title_and_dots(self):
        valid, msg = validate_name("Dr. R. K. Gupta", "Customer Name")
        assert valid is True
        assert msg == ""

    def test_name_too_short(self):
        valid, msg = validate_name("A", "Employee Name")
        assert valid is False
        assert "at least 2 characters" in msg

    def test_name_with_pure_numbers_fails(self):
        valid, msg = validate_name("12345", "Item Name")
        assert valid is False
        assert "contain alphabetic characters" in msg

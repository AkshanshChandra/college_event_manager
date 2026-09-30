def validate_10_digit_phone(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) != 10:
        raise ValueError("Phone number must have exactly 10 digits.")
    return digits

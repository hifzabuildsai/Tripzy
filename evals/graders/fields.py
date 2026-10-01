from typing import Any


def _normalized(value: Any) -> Any:
    if isinstance(value, str):
        return " ".join(value.split()).casefold()
    if isinstance(value, list):
        return [_normalized(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalized(item) for key, item in value.items()}
    return value


def grade_fields(
    actual: dict[str, Any],
    expected: dict[str, Any],
) -> dict[str, Any]:
    """Grade expected fields and penalize model-added fields."""

    expected_keys = set(expected)
    actual_keys = {
        key
        for key, value in actual.items()
        if value not in (None, [], {})
    }

    matched = {
        key
        for key in expected_keys.intersection(actual_keys)
        if _normalized(actual[key]) == _normalized(expected[key])
    }
    unexpected = actual_keys - expected_keys

    precision = (
        len(matched) / len(actual_keys)
        if actual_keys
        else (1.0 if not expected_keys else 0.0)
    )
    recall = (
        len(matched) / len(expected_keys)
        if expected_keys
        else 1.0
    )
    unrequested_rate = (
        len(unexpected) / len(actual_keys)
        if actual_keys
        else 0.0
    )

    return {
        "passed": matched == expected_keys and not unexpected,
        "precision": precision,
        "recall": recall,
        "unrequested_field_rate": unrequested_rate,
        "matched_fields": sorted(matched),
        "missing_fields": sorted(expected_keys - matched),
        "unexpected_fields": sorted(unexpected),
    }

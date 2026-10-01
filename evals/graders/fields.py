from typing import Any


INTEREST_FIELDS = {
    "interests_add",
    "interests_remove",
    "interests_replace",
}


def _normalized(value: Any) -> Any:
    if isinstance(value, str):
        return " ".join(value.split()).casefold()
    if isinstance(value, list):
        return [_normalized(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalized(item) for key, item in value.items()}
    return value


def _provided_fields(values: dict[str, Any]) -> set[str]:
    # Empty collection outputs are semantically omitted at the application
    # boundary (notably interests_replace=[] in the M18.3 regression).
    return {
        key
        for key, value in values.items()
        if value not in (None, [], {})
    }


def grade_fields(
    actual: dict[str, Any],
    expected: dict[str, Any],
) -> dict[str, Any]:
    """Grade extraction/correction fields without rewarding extra output."""

    expected_keys = _provided_fields(expected)
    actual_keys = _provided_fields(actual)

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

    expected_interest = expected_keys.intersection(INTEREST_FIELDS)
    actual_interest = actual_keys.intersection(INTEREST_FIELDS)
    interest_ok = (
        expected_interest == actual_interest
        and all(
            _normalized(actual[key]) == _normalized(expected[key])
            for key in expected_interest
        )
    )

    exact_match = matched == expected_keys and not unexpected

    return {
        "passed": exact_match,
        "field_precision": precision,
        "field_recall": recall,
        "exact_match": 1.0 if exact_match else 0.0,
        "unrequested_field_rate": unrequested_rate,
        "interest_operation_correctness": 1.0 if interest_ok else 0.0,
        "matched_fields": sorted(matched),
        "missing_fields": sorted(expected_keys - matched),
        "unexpected_fields": sorted(unexpected),
    }

import json
import csv
import io
from typing import Any, Optional, List


def json_to_csv(json_input: str | dict) -> str:
    """
    Convert JSON to flattened CSV format.

    Args:
        json_input: JSON string or dict. If the JSON has a 'results' key containing
                   a list, it will be extracted. Otherwise, the entire structure
                   will be wrapped in a list for processing.

    Returns:
        CSV string with headers and flattened rows
    """
    # Parse JSON if it's a string
    if isinstance(json_input, str):
        try:
            data = json.loads(json_input)
        except json.JSONDecodeError:
            # If JSON parsing fails, return empty CSV
            return ""
    else:
        data = json_input

    if isinstance(data, dict) and "results" in data:
        results_value = data["results"]
        # Handle both list and single object responses
        if isinstance(results_value, list):
            records = results_value
        elif isinstance(results_value, dict):
            # Single object response (e.g., get_last_trade returns results as object)
            records = [results_value]
        else:
            records = [results_value]
    elif isinstance(data, dict) and "last" in data:
        # Handle responses with "last" key (e.g., get_last_trade, get_last_quote)
        records = [data["last"]] if isinstance(data["last"], dict) else [data]
    elif isinstance(data, list):
        records = data
    else:
        records = [data]

    # Only flatten dict records, skip non-dict items
    flattened_records = []
    for record in records:
        if isinstance(record, dict):
            flattened_records.append(_flatten_dict(record))
        else:
            # If it's not a dict, wrap it in a dict with a 'value' key
            flattened_records.append({"value": str(record)})

    if not flattened_records:
        return ""

    # Get all unique keys across all records (for consistent column ordering)
    all_keys = []
    seen = set()
    for record in flattened_records:
        if isinstance(record, dict):
            for key in record.keys():
                if key not in seen:
                    all_keys.append(key)
                    seen.add(key)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=all_keys, lineterminator="\n")
    writer.writeheader()
    writer.writerows(flattened_records)

    return output.getvalue()


def _flatten_dict(
    d: dict[str, Any], parent_key: str = "", sep: str = "_"
) -> dict[str, Any]:
    """
    Flatten a nested dictionary by joining keys with separator.

    Args:
        d: Dictionary to flatten
        parent_key: Key from parent level (for recursion)
        sep: Separator to use between nested keys

    Returns:
        Flattened dictionary with no nested structures
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k

        if isinstance(v, dict):
            # Recursively flatten nested dicts
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Convert lists to comma-separated strings
            items.append((new_key, str(v)))
        else:
            items.append((new_key, v))

    return dict(items)


def json_to_csv_filtered(
    json_input: str | dict,
    fields: Optional[List[str]] = None,
    exclude_fields: Optional[List[str]] = None,
) -> str:
    """
    Convert JSON to CSV with optional field filtering.

    Args:
        json_input: JSON string or dict
        fields: Include only these fields (None = all)
        exclude_fields: Exclude these fields

    Returns:
        CSV string with selected fields only
    """
    # Parse JSON
    if isinstance(json_input, str):
        try:
            data = json.loads(json_input)
        except json.JSONDecodeError:
            return ""
    else:
        data = json_input

    # Extract records
    if isinstance(data, dict) and "results" in data:
        results_value = data["results"]
        if isinstance(results_value, list):
            records = results_value
        elif isinstance(results_value, dict):
            records = [results_value]
        else:
            records = [results_value]
    elif isinstance(data, dict) and "last" in data:
        records = [data["last"]] if isinstance(data["last"], dict) else [data]
    elif isinstance(data, list):
        records = data
    else:
        records = [data]

    # Flatten records
    flattened = []
    for record in records:
        if isinstance(record, dict):
            flattened.append(_flatten_dict(record))
        else:
            flattened.append({"value": str(record)})

    # Apply field filtering
    if fields:
        flattened = [
            {k: v for k, v in record.items() if k in fields} for record in flattened
        ]
    elif exclude_fields:
        flattened = [
            {k: v for k, v in record.items() if k not in exclude_fields}
            for record in flattened
        ]

    # Convert to CSV
    if not flattened:
        return ""

    # Get all unique keys across all records (for consistent column ordering)
    all_keys = []
    seen = set()
    for record in flattened:
        for key in record.keys():
            if key not in seen:
                all_keys.append(key)
                seen.add(key)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=all_keys, lineterminator="\n")
    writer.writeheader()
    writer.writerows(flattened)

    return output.getvalue()


def json_to_compact(json_input: str | dict, fields: Optional[List[str]] = None) -> str:
    """
    Convert JSON to minimal compact format.
    Best for single-record responses.

    Args:
        json_input: JSON string or dict
        fields: Include only these fields

    Returns:
        Compact JSON string (e.g., '{"close": 185.92, "volume": 52165200}')
    """
    if isinstance(json_input, str):
        try:
            data = json.loads(json_input)
        except json.JSONDecodeError:
            return "{}"
    else:
        data = json_input

    # Extract single record
    if isinstance(data, dict) and "results" in data:
        results = data["results"]
        if isinstance(results, list):
            record = results[0] if results else {}
        else:
            record = results
    elif isinstance(data, dict) and "last" in data:
        record = data["last"] if isinstance(data["last"], dict) else {}
    elif isinstance(data, list):
        record = data[0] if data else {}
    else:
        record = data

    # Flatten
    if isinstance(record, dict):
        flattened = _flatten_dict(record)
    else:
        flattened = {"value": str(record)}

    # Apply field filtering
    if fields:
        flattened = {k: v for k, v in flattened.items() if k in fields}

    return json.dumps(flattened, separators=(",", ":"))


def json_to_json_filtered(
    json_input: str | dict,
    fields: Optional[List[str]] = None,
    preserve_structure: bool = False,
) -> str:
    """
    Convert to JSON with optional field filtering.

    Args:
        json_input: JSON string or dict
        fields: Include only these fields
        preserve_structure: Keep nested structure (don't flatten)

    Returns:
        JSON string
    """
    if isinstance(json_input, str):
        try:
            data = json.loads(json_input)
        except json.JSONDecodeError:
            return "[]"
    else:
        data = json_input

    if isinstance(data, dict) and "results" in data:
        results_value = data["results"]
        if isinstance(results_value, list):
            records = results_value
        elif isinstance(results_value, dict):
            records = [results_value]
        else:
            records = [results_value]
    elif isinstance(data, dict) and "last" in data:
        records = [data["last"]] if isinstance(data["last"], dict) else [data]
    elif isinstance(data, list):
        records = data
    else:
        records = [data]

    if not preserve_structure:
        flattened = []
        for record in records:
            if isinstance(record, dict):
                flattened.append(_flatten_dict(record))
            else:
                flattened.append({"value": str(record)})
        records = flattened

    if fields:
        records = [
            {k: v for k, v in record.items() if k in fields} for record in records
        ]

    return json.dumps(records, indent=2)

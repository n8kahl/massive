"""
Output filtering module for MCP Massive server.

This module provides server-side filtering capabilities to reduce context token usage
by allowing field selection, output format selection, and row aggregation.
"""

import json
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Literal


# Field presets for common use cases
FIELD_PRESETS = {
    # Price presets
    "price": ["ticker", "close", "timestamp"],
    "last_price": ["close"],
    # OHLC presets
    "ohlc": ["ticker", "open", "high", "low", "close", "timestamp"],
    "ohlcv": ["ticker", "open", "high", "low", "close", "volume", "timestamp"],
    # Summary presets
    "summary": ["ticker", "close", "volume", "change_percent"],
    "minimal": ["ticker", "close"],
    # Volume presets
    "volume": ["ticker", "volume", "timestamp"],
    # Details presets
    "details": ["ticker", "name", "market", "locale", "primary_exchange"],
    "info": ["ticker", "name", "description", "homepage_url"],
    # News presets
    "news_headlines": ["title", "published_utc", "author"],
    "news_summary": ["title", "description", "published_utc", "article_url"],
    # Trade presets
    "trade": ["price", "size", "timestamp"],
    "quote": ["bid", "ask", "bid_size", "ask_size", "timestamp"],
    # Options presets (field names are flattened from nested API response)
    "greeks": ["details_ticker", "details_strike_price", "details_expiration_date", "details_contract_type",
               "greeks_delta", "greeks_gamma", "greeks_theta", "greeks_vega", "implied_volatility"],
    "options_summary": ["details_ticker", "details_strike_price", "details_expiration_date", "details_contract_type",
                        "day_close", "day_open", "day_volume", "open_interest", "implied_volatility"],
    "options_quote": ["details_ticker", "details_strike_price", "details_contract_type",
                      "last_quote_bid", "last_quote_ask", "last_quote_bid_size", "last_quote_ask_size"],
}


@dataclass
class FilterOptions:
    """Options for filtering MCP tool outputs."""

    # Field selection
    fields: Optional[List[str]] = None  # Include only these fields
    exclude_fields: Optional[List[str]] = None  # Exclude these fields

    # Output format
    format: Literal["csv", "json", "compact"] = "csv"

    # Aggregation
    aggregate: Optional[Literal["first", "last"]] = None

    # Row filtering (future enhancement)
    conditions: Optional[Dict[str, Any]] = None  # {"volume_gt": 1000000}


def parse_filter_params(
    fields: Optional[str] = None,
    output_format: str = "csv",
    aggregate: Optional[str] = None,
) -> FilterOptions:
    """
    Parse tool parameters into FilterOptions.

    Args:
        fields: Comma-separated field names or preset name (e.g., "ticker,close" or "preset:price")
        output_format: Desired output format ("csv", "json", or "compact")
        aggregate: Aggregation method ("first", "last", or None)

    Returns:
        FilterOptions instance
    """
    # Parse fields parameter
    field_list = None
    if fields:
        # Check if it's a preset
        if fields.startswith("preset:"):
            preset_name = fields[7:]  # Remove "preset:" prefix
            field_list = FIELD_PRESETS.get(preset_name)
            if field_list is None:
                raise ValueError(
                    f"Unknown preset: {preset_name}. Available presets: {', '.join(FIELD_PRESETS.keys())}"
                )
        else:
            # Parse comma-separated fields
            field_list = [f.strip() for f in fields.split(",") if f.strip()]

    # Validate output format
    if output_format not in ["csv", "json", "compact"]:
        raise ValueError(
            f"Invalid output_format: {output_format}. Must be 'csv', 'json', or 'compact'"
        )

    # Validate aggregate
    if aggregate and aggregate not in ["first", "last"]:
        raise ValueError(
            f"Invalid aggregate: {aggregate}. Must be 'first', 'last', or None"
        )

    return FilterOptions(
        fields=field_list,
        format=output_format,
        aggregate=aggregate,
    )


def apply_filters(data: dict | str, options: FilterOptions) -> str:
    """
    Apply filtering to API response data.

    Args:
        data: JSON string or dict from Massive API
        options: Filtering options to apply

    Returns:
        Filtered and formatted string response
    """
    # Import formatters here to avoid circular imports
    from .formatters import (
        json_to_csv_filtered,
        json_to_compact,
        json_to_json_filtered,
    )

    # Parse JSON if it's a string
    if isinstance(data, str):
        parsed_data = json.loads(data)
    else:
        parsed_data = data

    # Apply aggregation if specified
    if options.aggregate:
        parsed_data = _apply_aggregation(parsed_data, options.aggregate)

    # Route to appropriate formatter based on output format
    if options.format == "csv":
        return json_to_csv_filtered(
            parsed_data,
            fields=options.fields,
            exclude_fields=options.exclude_fields,
        )
    elif options.format == "json":
        return json_to_json_filtered(
            parsed_data,
            fields=options.fields,
        )
    elif options.format == "compact":
        return json_to_compact(
            parsed_data,
            fields=options.fields,
        )
    else:
        raise ValueError(f"Unsupported format: {options.format}")


def _apply_aggregation(data: dict | list, method: str) -> dict | list:
    """
    Apply aggregation to extract a single record.

    Args:
        data: JSON data (dict or list)
        method: Aggregation method ("first" or "last")

    Returns:
        Aggregated data
    """
    # Extract records
    if isinstance(data, dict) and "results" in data:
        records = data["results"]
    elif isinstance(data, list):
        records = data
    else:
        # Single record, return as-is
        return data

    if not records:
        return data

    # Apply aggregation
    if method == "first":
        aggregated_record = records[0]
    elif method == "last":
        aggregated_record = records[-1]
    else:
        raise ValueError(f"Unknown aggregation method: {method}")

    # Preserve structure
    if isinstance(data, dict) and "results" in data:
        return {**data, "results": [aggregated_record]}
    else:
        return [aggregated_record]

"""Tests for the filters module."""

import json
import pytest

from mcp_massive.filters import (
    FIELD_PRESETS,
    FilterOptions,
    parse_filter_params,
    apply_filters,
    _apply_aggregation,
)


class TestFieldPresets:
    """Tests for the FIELD_PRESETS configuration."""

    def test_greeks_preset_exists(self):
        """Test that greeks preset exists with expected fields."""
        assert "greeks" in FIELD_PRESETS
        preset = FIELD_PRESETS["greeks"]
        assert "details_strike_price" in preset
        assert "details_contract_type" in preset
        assert "greeks_delta" in preset
        assert "greeks_gamma" in preset
        assert "greeks_theta" in preset
        assert "greeks_vega" in preset
        assert "implied_volatility" in preset

    def test_options_summary_preset_exists(self):
        """Test that options_summary preset exists with expected fields."""
        assert "options_summary" in FIELD_PRESETS
        preset = FIELD_PRESETS["options_summary"]
        assert "details_strike_price" in preset
        assert "details_expiration_date" in preset
        assert "details_contract_type" in preset
        assert "day_volume" in preset
        assert "open_interest" in preset

    def test_options_quote_preset_exists(self):
        """Test that options_quote preset exists with expected fields."""
        assert "options_quote" in FIELD_PRESETS
        preset = FIELD_PRESETS["options_quote"]
        assert "details_strike_price" in preset
        assert "last_quote_bid" in preset
        assert "last_quote_ask" in preset

    def test_price_presets_exist(self):
        """Test that basic price presets exist."""
        assert "price" in FIELD_PRESETS
        assert "ohlc" in FIELD_PRESETS
        assert "ohlcv" in FIELD_PRESETS


class TestParseFilterParams:
    """Tests for the parse_filter_params function."""

    def test_parse_comma_separated_fields(self):
        """Test parsing comma-separated field names."""
        options = parse_filter_params(fields="ticker,close,volume")
        assert options.fields == ["ticker", "close", "volume"]

    def test_parse_preset_fields(self):
        """Test parsing preset field names."""
        options = parse_filter_params(fields="preset:greeks")
        assert options.fields == FIELD_PRESETS["greeks"]

    def test_parse_unknown_preset_raises_error(self):
        """Test that unknown presets raise ValueError."""
        with pytest.raises(ValueError, match="Unknown preset"):
            parse_filter_params(fields="preset:unknown_preset")

    def test_parse_output_format_csv(self):
        """Test parsing CSV output format."""
        options = parse_filter_params(output_format="csv")
        assert options.format == "csv"

    def test_parse_output_format_json(self):
        """Test parsing JSON output format."""
        options = parse_filter_params(output_format="json")
        assert options.format == "json"

    def test_parse_output_format_compact(self):
        """Test parsing compact output format."""
        options = parse_filter_params(output_format="compact")
        assert options.format == "compact"

    def test_parse_invalid_output_format_raises_error(self):
        """Test that invalid output formats raise ValueError."""
        with pytest.raises(ValueError, match="Invalid output_format"):
            parse_filter_params(output_format="xml")

    def test_parse_aggregate_first(self):
        """Test parsing 'first' aggregation."""
        options = parse_filter_params(aggregate="first")
        assert options.aggregate == "first"

    def test_parse_aggregate_last(self):
        """Test parsing 'last' aggregation."""
        options = parse_filter_params(aggregate="last")
        assert options.aggregate == "last"

    def test_parse_invalid_aggregate_raises_error(self):
        """Test that invalid aggregation raises ValueError."""
        with pytest.raises(ValueError, match="Invalid aggregate"):
            parse_filter_params(aggregate="average")

    def test_parse_none_fields(self):
        """Test that None fields is preserved."""
        options = parse_filter_params(fields=None)
        assert options.fields is None

    def test_parse_whitespace_in_fields(self):
        """Test that whitespace is stripped from field names."""
        options = parse_filter_params(fields=" ticker , close , volume ")
        assert options.fields == ["ticker", "close", "volume"]


class TestApplyAggregation:
    """Tests for the _apply_aggregation helper function."""

    def test_aggregate_first_from_results(self):
        """Test extracting first record from results list."""
        data = {"results": [{"a": 1}, {"a": 2}, {"a": 3}]}
        result = _apply_aggregation(data, "first")
        assert result == {"results": [{"a": 1}]}

    def test_aggregate_last_from_results(self):
        """Test extracting last record from results list."""
        data = {"results": [{"a": 1}, {"a": 2}, {"a": 3}]}
        result = _apply_aggregation(data, "last")
        assert result == {"results": [{"a": 3}]}

    def test_aggregate_first_from_list(self):
        """Test extracting first record from plain list."""
        data = [{"a": 1}, {"a": 2}]
        result = _apply_aggregation(data, "first")
        assert result == [{"a": 1}]

    def test_aggregate_last_from_list(self):
        """Test extracting last record from plain list."""
        data = [{"a": 1}, {"a": 2}]
        result = _apply_aggregation(data, "last")
        assert result == [{"a": 2}]

    def test_aggregate_single_record_unchanged(self):
        """Test that single non-list record is unchanged."""
        data = {"ticker": "AAPL", "price": 150}
        result = _apply_aggregation(data, "first")
        assert result == data

    def test_aggregate_empty_results(self):
        """Test aggregation of empty results."""
        data = {"results": []}
        result = _apply_aggregation(data, "first")
        assert result == {"results": []}


class TestApplyFilters:
    """Tests for the apply_filters function."""

    def test_apply_field_filter_csv(self):
        """Test applying field filter with CSV output."""
        data = {"results": [{"ticker": "AAPL", "price": 150, "volume": 1000}]}
        options = FilterOptions(fields=["ticker", "price"], format="csv")
        result = apply_filters(data, options)
        assert "ticker" in result
        assert "price" in result
        assert "volume" not in result

    def test_apply_field_filter_json(self):
        """Test applying field filter with JSON output."""
        data = {"results": [{"ticker": "AAPL", "price": 150, "volume": 1000}]}
        options = FilterOptions(fields=["ticker", "price"], format="json")
        result = apply_filters(data, options)
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["ticker"] == "AAPL"
        assert parsed[0]["price"] == 150
        assert "volume" not in parsed[0]

    def test_apply_compact_format(self):
        """Test applying compact format."""
        data = {"results": [{"ticker": "AAPL", "price": 150}]}
        options = FilterOptions(format="compact")
        result = apply_filters(data, options)
        # Compact format should be a compact JSON string
        assert '"ticker"' in result or '"price"' in result

    def test_apply_aggregation_and_filter(self):
        """Test combining aggregation with field filtering."""
        data = {
            "results": [
                {"ticker": "AAPL", "price": 150},
                {"ticker": "GOOGL", "price": 2800},
            ]
        }
        options = FilterOptions(fields=["ticker"], aggregate="last", format="json")
        result = apply_filters(data, options)
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["ticker"] == "GOOGL"

    def test_apply_filters_from_json_string(self):
        """Test applying filters to JSON string input."""
        data = '{"results": [{"ticker": "AAPL", "price": 150}]}'
        options = FilterOptions(fields=["ticker"], format="json")
        result = apply_filters(data, options)
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["ticker"] == "AAPL"


class TestFilterOptionsDataclass:
    """Tests for the FilterOptions dataclass."""

    def test_default_values(self):
        """Test default values of FilterOptions."""
        options = FilterOptions()
        assert options.fields is None
        assert options.exclude_fields is None
        assert options.format == "csv"
        assert options.aggregate is None
        assert options.conditions is None

    def test_custom_values(self):
        """Test custom values of FilterOptions."""
        options = FilterOptions(
            fields=["a", "b"],
            exclude_fields=["c"],
            format="json",
            aggregate="first",
        )
        assert options.fields == ["a", "b"]
        assert options.exclude_fields == ["c"]
        assert options.format == "json"
        assert options.aggregate == "first"

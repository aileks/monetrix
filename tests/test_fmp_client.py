import json
import unittest
from unittest.mock import patch

import requests

from monetrix.api_clients import fmp_client


class DummyResponse:
    def __init__(
        self,
        status_code: int,
        payload: object | None = None,
        json_exc: Exception | None = None,
        text: str = "",
    ) -> None:
        self.status_code = status_code
        self._payload = payload
        self._json_exc = json_exc
        self.text = text

    def json(self) -> object:
        if self._json_exc is not None:
            raise self._json_exc
        return self._payload


class FmpClientTests(unittest.TestCase):
    def setUp(self) -> None:
        for fn in [
            fmp_client.get_stock_quote,
            fmp_client.get_historical_price_data,
            fmp_client.get_market_winners,
            fmp_client.get_market_losers,
            fmp_client.get_technical_indicator_result,
            fmp_client.get_technical_indicator,
            fmp_client.get_multiple_stock_quotes,
            fmp_client.get_forex_pairs_list,
            fmp_client.get_forex_quote,
        ]:
            if hasattr(fn, "clear"):
                fn.clear()

    def test_get_stock_quote_maps_auth_error(self) -> None:
        response = DummyResponse(
            401,
            {
                "Error Message": (
                    "Invalid API KEY. Feel free to create a Free API Key."
                )
            },
        )

        with patch("monetrix.api_clients.fmp_client.requests.get", return_value=response):
            result = fmp_client.get_stock_quote("AAPL", "bad-key")

        self.assertFalse(result.ok)
        self.assertEqual(result.category, "auth")
        self.assertEqual(result.status_code, 401)

    def test_get_stock_quote_uses_stable_endpoint(self) -> None:
        response = DummyResponse(200, [{"symbol": "AAPL", "price": 100.0}])

        with patch(
            "monetrix.api_clients.fmp_client.requests.get",
            return_value=response,
        ) as mock_get:
            fmp_client.get_stock_quote("AAPL", "key")

        request_url = mock_get.call_args.args[0]
        self.assertIn("/stable/quote?", request_url)
        self.assertIn("symbol=AAPL", request_url)

    def test_get_stock_quote_maps_rate_limit(self) -> None:
        response = DummyResponse(429, {"Error Message": "Rate limit reached"})

        with patch("monetrix.api_clients.fmp_client.requests.get", return_value=response):
            result = fmp_client.get_stock_quote("AAPL", "key")

        self.assertFalse(result.ok)
        self.assertEqual(result.category, "rate_limit")
        self.assertEqual(result.status_code, 429)

    def test_get_stock_quote_maps_empty_data(self) -> None:
        response = DummyResponse(200, [])

        with patch("monetrix.api_clients.fmp_client.requests.get", return_value=response):
            result = fmp_client.get_stock_quote("AAPL", "key")

        self.assertFalse(result.ok)
        self.assertEqual(result.category, "empty")

    def test_get_stock_quote_success(self) -> None:
        response = DummyResponse(200, [{"symbol": "AAPL", "price": 100.0}])

        with patch("monetrix.api_clients.fmp_client.requests.get", return_value=response):
            result = fmp_client.get_stock_quote("AAPL", "key")

        self.assertTrue(result.ok)
        if not isinstance(result.data, dict):
            self.fail("expected quote payload dict")
        self.assertEqual(result.data["symbol"], "AAPL")

    def test_get_stock_quote_maps_decode_error(self) -> None:
        response = DummyResponse(
            200,
            json_exc=json.JSONDecodeError("bad json", "<html>", 0),
        )

        with patch("monetrix.api_clients.fmp_client.requests.get", return_value=response):
            result = fmp_client.get_stock_quote("AAPL", "key")

        self.assertFalse(result.ok)
        self.assertEqual(result.category, "decode")

    def test_get_stock_quote_maps_network_error(self) -> None:
        with patch(
            "monetrix.api_clients.fmp_client.requests.get",
            side_effect=requests.exceptions.Timeout("timeout"),
        ):
            result = fmp_client.get_stock_quote("AAPL", "key")

        self.assertFalse(result.ok)
        self.assertEqual(result.category, "network")

    def test_market_winners_empty_list_is_not_error(self) -> None:
        response = DummyResponse(200, [])

        with patch("monetrix.api_clients.fmp_client.requests.get", return_value=response):
            result = fmp_client.get_market_winners("key")

        self.assertTrue(result.ok)
        self.assertEqual(result.data, [])

    def test_market_winners_uses_stable_endpoint(self) -> None:
        response = DummyResponse(200, [])

        with patch(
            "monetrix.api_clients.fmp_client.requests.get",
            return_value=response,
        ) as mock_get:
            fmp_client.get_market_winners("key")

        request_url = mock_get.call_args.args[0]
        self.assertIn("/stable/biggest-gainers?", request_url)

    def test_market_winners_auth_is_error(self) -> None:
        response = DummyResponse(401, {"Error Message": "Invalid API KEY"})

        with patch("monetrix.api_clients.fmp_client.requests.get", return_value=response):
            result = fmp_client.get_market_winners("key")

        self.assertFalse(result.ok)
        self.assertEqual(result.category, "auth")

    def test_format_api_error_includes_diagnostics(self) -> None:
        result = fmp_client.FMPResponse(
            ok=False,
            category="auth",
            status_code=401,
            message="Invalid API KEY",
        )

        formatted = fmp_client.format_api_error(result, "fallback")

        self.assertIn("unauthorized", formatted.lower())
        self.assertIn("status 401", formatted)

    def test_legacy_endpoint_error_gets_specific_message(self) -> None:
        result = fmp_client.FMPResponse(
            ok=False,
            category="auth",
            status_code=403,
            message="Legacy Endpoint : this endpoint is only available for legacy users",
        )

        formatted = fmp_client.format_api_error(result, "fallback")

        self.assertIn("legacy endpoint", formatted.lower())
        self.assertIn("status 403", formatted)

    def test_batch_quotes_uses_stable_endpoint(self) -> None:
        response = DummyResponse(200, [{"symbol": "AAPL", "price": 100.0}])

        with patch(
            "monetrix.api_clients.fmp_client.requests.get",
            return_value=response,
        ) as mock_get:
            fmp_client.get_multiple_stock_quotes("key", ["AAPL", "MSFT"])

        request_url = mock_get.call_args.args[0]
        self.assertIn("/stable/batch-quote?", request_url)
        self.assertIn("symbols=AAPL%2CMSFT", request_url)

    def test_technical_indicator_uses_stable_endpoint(self) -> None:
        response = DummyResponse(200, [{"date": "2025-01-01", "rsi": 52.0}])

        with patch(
            "monetrix.api_clients.fmp_client.requests.get",
            return_value=response,
        ) as mock_get:
            series = fmp_client.get_technical_indicator("key", "AAPL", 14, "rsi")

        self.assertIsNotNone(series)
        request_url = mock_get.call_args.args[0]
        self.assertIn("/stable/technical-indicators/rsi?", request_url)
        self.assertIn("periodLength=14", request_url)
        self.assertIn("timeframe=1day", request_url)

    def test_technical_indicator_plan_error_maps_category(self) -> None:
        response = DummyResponse(
            402,
            json_exc=json.JSONDecodeError("bad json", "<html>", 0),
            text="<html>Subscription required</html>",
        )

        with patch(
            "monetrix.api_clients.fmp_client.requests.get",
            return_value=response,
        ):
            result = fmp_client.get_technical_indicator_result(
                "key",
                "AAPL",
                14,
                "rsi",
            )

        self.assertFalse(result.ok)
        self.assertEqual(result.category, "plan")
        self.assertEqual(result.status_code, 402)

    def test_format_api_error_for_plan(self) -> None:
        result = fmp_client.FMPResponse(
            ok=False,
            category="plan",
            status_code=402,
            message="Subscription required",
        )

        formatted = fmp_client.format_api_error(result, "fallback")

        self.assertIn("subscription tier", formatted.lower())
        self.assertIn("status 402", formatted)

    def test_technical_indicator_parses_nested_payload_key(self) -> None:
        response = DummyResponse(
            200,
            {"technicalIndicator": [{"date": "2025-01-01", "rsi": 52.0}]},
        )

        with patch(
            "monetrix.api_clients.fmp_client.requests.get",
            return_value=response,
        ):
            series = fmp_client.get_technical_indicator("key", "AAPL", 14, "rsi")

        self.assertIsNotNone(series)

    def test_technical_indicator_falls_back_to_period_param(self) -> None:
        first_response = DummyResponse(404, {"message": "Not Found"})
        second_response = DummyResponse(200, [{"date": "2025-01-01", "rsi": 51.0}])

        with patch(
            "monetrix.api_clients.fmp_client.requests.get",
            side_effect=[first_response, second_response],
        ) as mock_get:
            series = fmp_client.get_technical_indicator("key", "AAPL", 14, "rsi")

        self.assertIsNotNone(series)
        first_url = mock_get.call_args_list[0].args[0]
        second_url = mock_get.call_args_list[1].args[0]
        self.assertIn("periodLength=14", first_url)
        self.assertIn("period=14", second_url)

    def test_forex_pair_list_uses_stable_endpoint(self) -> None:
        response = DummyResponse(200, [{"symbol": "EURUSD"}])

        with patch(
            "monetrix.api_clients.fmp_client.requests.get",
            return_value=response,
        ) as mock_get:
            result = fmp_client.get_forex_pairs_list("key")

        self.assertTrue(result.ok)
        self.assertEqual(result.data, ["EURUSD"])
        request_url = mock_get.call_args.args[0]
        self.assertIn("/stable/forex-list?", request_url)


if __name__ == "__main__":
    unittest.main()

import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from monetrix import config


class ResolveFmpApiKeyTests(unittest.TestCase):
    def test_prefers_flat_secret_over_env(self) -> None:
        fake_st = SimpleNamespace(secrets={"FMP_API_KEY": "  secret-key  "})

        with patch.object(config, "st", fake_st), patch.dict(
            os.environ,
            {"FMP_API_KEY": "env-key"},
            clear=True,
        ):
            self.assertEqual(config.resolve_fmp_api_key(), "secret-key")

    def test_reads_nested_secret(self) -> None:
        fake_st = SimpleNamespace(secrets={"fmp": {"api_key": "nested-key"}})

        with patch.object(config, "st", fake_st), patch.dict(os.environ, {}, clear=True):
            self.assertEqual(config.resolve_fmp_api_key(), "nested-key")

    def test_falls_back_to_env_and_trims_quotes(self) -> None:
        fake_st = SimpleNamespace(secrets={})

        with patch.object(config, "st", fake_st), patch.dict(
            os.environ,
            {"FMP_API_KEY": "  'env-key'  "},
            clear=True,
        ):
            self.assertEqual(config.resolve_fmp_api_key(), "env-key")

    def test_returns_none_for_empty_values(self) -> None:
        fake_st = SimpleNamespace(secrets={"FMP_API_KEY": "   "})

        with patch.object(config, "st", fake_st), patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(config.resolve_fmp_api_key())

    def test_falls_back_to_env_when_streamlit_secrets_missing(self) -> None:
        class MissingSecrets:
            @property
            def secrets(self) -> object:
                raise RuntimeError("no secrets.toml")

        with patch.object(config, "st", MissingSecrets()), patch.dict(
            os.environ,
            {"FMP_API_KEY": "env-only-key"},
            clear=True,
        ):
            self.assertEqual(config.resolve_fmp_api_key(), "env-only-key")


if __name__ == "__main__":
    unittest.main()

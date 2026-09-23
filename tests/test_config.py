import os
import unittest
from unittest.mock import patch

from config import ConfigurationError, Settings


class SettingsTests(unittest.TestCase):
    def environment(self, **overrides):
        values = {
            "USERNAME": "test-user",
            "PASSWORD": "test-password",
            "LOTTO645_COUNT": "1",
            "BUY_LOTTO645": "true",
            "BUY_WIN720": "false",
            "CHECK_LOTTO645": "true",
            "CHECK_WIN720": "true",
            "MAX_WEEKLY_SPEND": "1000",
        }
        values.update(overrides)
        return patch.dict(os.environ, values, clear=True)

    def test_default_lotto_only_plan_is_within_budget(self):
        with self.environment():
            settings = Settings.from_environment()
        self.assertEqual(settings.weekly_purchase_cost(), 1_000)
        settings.validate_weekly_purchase()

    def test_budget_blocks_unexpected_purchase_size(self):
        with self.environment(LOTTO645_COUNT="5", BUY_WIN720="true", MAX_WEEKLY_SPEND="5000"):
            settings = Settings.from_environment()
        with self.assertRaises(ConfigurationError):
            settings.validate_weekly_purchase()

    def test_credentials_are_required(self):
        with self.environment(USERNAME=""):
            with self.assertRaises(ConfigurationError):
                Settings.from_environment()

import json
import os
import tempfile
import unittest
from unittest.mock import patch

import state_store


class StateStoreTests(unittest.TestCase):
    def test_round_status_is_persisted_and_read(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"LOTTERY_STATE_DIR": directory}, clear=True):
                state_store.record_round("purchases", "1201", "confirmed", source="lottery_ledger")
                entry = state_store.get_round("purchases", "1201")

                self.assertEqual(entry["status"], "confirmed")
                self.assertEqual(entry["source"], "lottery_ledger")
                self.assertIsNone(state_store.get_round("purchases", "1202"))

                with open(f"{directory}/purchases.json", encoding="utf-8") as state_file:
                    self.assertEqual(json.load(state_file)["rounds"]["1201"]["status"], "confirmed")

    def test_store_is_optional_without_state_directory(self):
        with patch.dict(os.environ, {}, clear=True):
            state_store.record_round("purchases", "1201", "confirmed", source="lottery_ledger")
            self.assertIsNone(state_store.get_round("purchases", "1201"))


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import Mock, patch

from lotto645 import Lotto645


class PurchaseGuardTests(unittest.TestCase):
    @patch("lotto645.HttpClientSingleton.get_instance")
    @patch.object(Lotto645, "_generate_req_headers", return_value={})
    def test_find_ticket_for_target_round(self, _headers, get_instance):
        client = Mock()
        client.get.return_value.json.return_value = {
            "data": {"list": [{"ltEpsd": "1201"}, {"ltEpsdView": "1202회"}]}
        }
        get_instance.return_value = client
        lotto = Lotto645()
        ticket = lotto.find_ticket_for_round(Mock(), "1202")

        self.assertEqual(ticket["ltEpsdView"], "1202회")

    @patch("lotto645.HttpClientSingleton.get_instance")
    @patch.object(Lotto645, "_generate_req_headers", return_value={})
    def test_missing_target_round_allows_a_future_attempt(self, _headers, get_instance):
        client = Mock()
        client.get.return_value.json.return_value = {"data": {"list": [{"ltEpsd": "1201"}]}}
        get_instance.return_value = client
        lotto = Lotto645()
        self.assertIsNone(lotto.find_ticket_for_round(Mock(), "1202"))


if __name__ == "__main__":
    unittest.main()

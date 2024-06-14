import unittest
from D1py import D1py

class TestD1py(unittest.TestCase):
    def setUp(self):
        self.account_id = "your_account_id"
        self.api_token = "your_api_token"
        self.d1 = D1py(self.account_id, self.api_token)

    def test_list_db(self):
        response = self.d1.list_db()
        self.assertIn('success', response)

if __name__ == '__main__':
    unittest.main()
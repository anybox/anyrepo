import unittest

import issuebot


class IssuebotTestCase(unittest.TestCase):

    def setUp(self):
        self.app = issuebot.app.test_client()

    def test_index(self):
        rv = self.app.get('/')
        self.assertIn('Welcome to issuebot', rv.data.decode())


if __name__ == '__main__':
    unittest.main()

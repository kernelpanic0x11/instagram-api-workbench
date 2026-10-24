"""Test the one-use browser form with synthetic codes on a local socket."""
import http.client
import unittest
from urllib.parse import urlencode
from mfa_form import LocalMfaForm


class MfaFormTests(unittest.TestCase):
    def setUp(self):
        self.form = LocalMfaForm(port=0)

    def tearDown(self):
        self.form.close()

    def submit(self, origin=None, token=None):
        connection = http.client.HTTPConnection(self.form.address, timeout=2)
        connection.request('POST', '/code', urlencode({'token': token or self.form.token, 'code': '123456'}),
                           {'Origin': origin or self.form.origin, 'Content-Type': 'application/x-www-form-urlencoded'})
        response = connection.getresponse()
        status, body = response.status, response.read()
        connection.close()
        return status, body

    def test_accepts_one_code_only_while_waiting_and_clears_it(self):
        self.assertEqual(self.submit()[0], 409)
        self.form.state = 'waiting'
        self.assertEqual(self.submit()[0], 200)
        self.assertEqual(self.form.state, 'verifying')
        self.assertEqual(self.submit()[0], 409)
        # Consume the code as the waiting authentication thread would.
        with self.form.lock:
            code, self.form.code = self.form.code, None
        self.assertEqual(code, '123456')
        self.assertIsNone(self.form.code)

    def test_cross_origin_and_missing_token_are_rejected(self):
        self.form.state = 'waiting'
        self.assertEqual(self.submit(origin='https://untrusted.invalid')[0], 403)
        self.assertEqual(self.submit(token='incorrect')[0], 400)
        self.assertIsNone(self.form.code)

    def test_timeout_expires_form(self):
        with self.assertRaises(TimeoutError):
            self.form.wait_for_code(timeout=0)
        self.assertEqual(self.form.state, 'expired')
        self.assertEqual(self.submit()[0], 409)


if __name__ == '__main__':
    unittest.main()

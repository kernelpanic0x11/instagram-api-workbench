"""Worker input boundary checks, without requests/instagrapi or network access."""
import base64
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('worker',Path(__file__).with_name('mobile-http-transport.py'))
worker=importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


class MobileTransportTests(unittest.TestCase):
    def request(self,**changes):
        return {'url':'https://i.instagram.com/api/v1/example/','method':'GET','headers':{},'body':'',**changes}

    def test_fixed_https_host_and_transport_headers(self):
        self.assertEqual(worker.validate_request(self.request()),b'')
        for url in ['http://i.instagram.com/','https://untrusted.invalid/','https://user@i.instagram.com/','https://i.instagram.com:444/']:
            with self.assertRaises(ValueError):worker.validate_request(self.request(url=url))
        for name in ['Host','Connection','Content-Length','Transfer-Encoding']:
            with self.assertRaises(ValueError):worker.validate_request(self.request(headers={name:'synthetic'}))

    def test_body_integrity_limits_and_header_injection(self):
        body=base64.b64encode(b'a=b').decode()
        self.assertEqual(worker.validate_request(self.request(method='POST',body=body)),b'a=b')
        with self.assertRaises(ValueError):worker.validate_request(self.request(body=body))
        with self.assertRaises(ValueError):worker.validate_request(self.request(headers={'X-Mid':'bad\r\nvalue'}))
        with self.assertRaises(ValueError):worker.validate_request(self.request(method='TRACE'))


if __name__=='__main__':unittest.main()

import re
import unittest

from common import upload_to


class UploadTestCase(unittest.TestCase):
    def test_upload_to(self):
        self.assertRegexpMatches(upload_to('this/is/the/path', None, 'duck.png'),
                                 'this/is/the/path/\w{2}/\w{2}/(\w{8}-\w{4}-\w{4}-\w{4}-\w{12})\.png')

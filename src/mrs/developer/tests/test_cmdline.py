import os
import sphinx.testing
import mrs.developer.testing
import unittest2 as unittest

def test_suite():
    return sphinx.testing.SphinxTestSuite([
            os.path.join(os.path.dirname(__file__), '..', 'distributions.txt'),
            ], layer=mrs.developer.testing.MRS_DEVELOPER_FIXTURE)

if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())


import os
import sphinx.testing


def test_suite():
    return sphinx.testing.SphinxTestSuite([
            os.path.join(os.path.dirname(__file__), '..', 'tests.txt'),
            ])

if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())


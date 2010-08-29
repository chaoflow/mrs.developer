import unittest
import manuel.codeblock
import manuel.doctest
import manuel.testing
import bashblock

def test_suite():
    m = manuel.doctest.Manuel()
    m += manuel.codeblock.Manuel()
    m += bashblock.Manuel()
    return manuel.testing.TestSuite(m, 'tests.txt')

if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())


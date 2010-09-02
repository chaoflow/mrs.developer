try:
    import unittest2 as unittest
except ImportError:
    import unittest

import os

from mrs.developer.node import LazyNode
from mrs.developer.node import File
from mrs.developer.node import Directory


class LazyNodeTest(unittest.TestCase):

    def test_init(self):
        node1 = LazyNode()
        node2 = LazyNode('with-name')
        self.assertEqual(node1.__name__, None)
        self.assertEqual(node2.__name__, 'with-name')

    def test_directory(self):
        test_skel = os.path.join(os.path.dirname(__file__), 'test_skel')
        node1 = Directory(test_skel)

        # lazy loading of elements
        self.assertEqual(node1._keys, None)
        self.assertIsInstance(node1['buildout.cfg'], File)
        self.assertEqual(node1['buildout.cfg'].__name__, 'buildout.cfg')
        self.assertEqual(sorted(node1._keys.keys()),
                         ['bootstrap.py', 'buildout.cfg', 'init.cfg'])




def test_suite():
    return unittest.TestLoader().loadTestsFromTestCase(LazyNodeTest)


if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())

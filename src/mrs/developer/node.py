"""Some basic nodes to be moved/merged with zodict

Everybody should once write a node from scratch...
"""

from zope.location import locate
from zope.location import LocationIterator

class Node(object):
    """Stuff we expect from our base of all bases
    """
    def __init__(self, name=None):
        self.__name__ = __name__
        self._keys = None

    def __iter__(self):
        try:
            return self._keys.__iter__()
        except AttributeError:
            self._keys = odict()
            self._load_keys()
            return self._keys.__iter__()

    def keys(self):
        return [x for x in self.__iter__()]

    @property
    def path(self):
        path = list()
        for parent in LocationIterator(self):
            path.append(parent.__name__)
        path.reverse()
        return path

    @property
    def root(self):
        root = None
        for parent in LocationIterator(self):
            root = parent
        return root


class FSNode(Node):
    """A directory or file on the local filesystem
    """
    @property
    def path(self):
        """The path of a local filesystem node is a string
        """
        return os.path.join(super(FSNode, self).path)


class File(FSNode):
    """A file in the filesystem
    """
    def __iter__(self):
        handle = open(self.path)
        for line in handle:
            yield line
        handle.close()


class Directory(FSNode):
    """A directory with possibly blacklisted content
    """
    blacklist = ('.', '..')

    def _load_keys(self):
        """The items in a directory are already unique
        """
        for key in os.listdir(self.path):
            if self.blacklisted(key):
                continue
            # XXX: _nil? so we can have a "child" with value None
            # keep in mind that .attrs is also a Node
            self.keys[key] = None

    def blacklisted(self, key):
        return key in self.blacklist

    def __getitem__(self, key):
        try:
            val = self._keys[key]
        except TypeError:
            iter(self)
        except KeyError:
            pass

        path = os.path.join(self.path, key)
        if os.path.isdir(path):
            val = Directory(key)
        elif os.path.isfile(path):
            val = File(key)
        val.__parent__ = self
        return self._keys[key] = val

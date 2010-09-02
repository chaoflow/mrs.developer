import os

from mrs.developer.base import Cmd
from mrs.developer.base import logger
from mrs.developer.node import Directory
from mrs.developer.node import File
from mrs.developer.node import FSNode
from mrs.developer.node import LazyNode



class Distribution(LazyNode):
    """A distribution
    """
    

class SDist(Distribution):
    """A source distribution
    """


class BDist(Distribution):
    """A binary distribution
    """


def distFromPath(path):
    """Create distribution object living at path in the filesystem

    Path can be
    - a zipped file ending in .egg (zipped binary distribution)
    - a directory ending in .egg (unzipped binary distribution)
    - unspported
    """
    if not os.path.isdir(path):
        msg = 'No distributions in singular files yet: %s.' % (path,)
        logger.error(msg)
        raise RuntimeError(msg)
    if not path.endswith('.egg'):
        msg = 'Only bdists ending in .egg so far: %s.' % (path,)
        logger.error(msg)
        raise RuntimeError(msg)
    return Bdist(path)
        

class PyScript(FSNode):
    """A channel that returns distributions used by a python script
    """
    def _iterchildkeys(self):
        """Our keys are the paths to distributions used by our script
        """
        consume = False
        for line in File(self.fspath):
            line = line.strip()
            if line.startswith('sys.path[0:0] = ['):
                consume = True
                continue
            elif line == ']':
                break
            elif not consume:
                continue
            # The key is the full path to the distribution
            key = line[1:-2]
            if not key.endswith('.egg'):
                logger.warn("Ignoring yet unsupported distribution in '%s'." \
                        % (key,))
                continue
            elif not os.path.isdir(key):
                logger.warn("Ignoring yet unsupported zipped bdist in '%s'." \
                        % (key,))
                continue
            yield key

    def _createchild(self, path):
        return distFromPath(path)


class PyScriptDir(FSNode):
    """A channel for all distributions from python scripts in a file
    """
    def _iterchildkeys(self):
        self.seen = {}
        for item in Directory(self.fspath).values():
            if os.path.isdir(item.fspath):
                for key in PyScriptDir(item.fspath):
                    if key not in self.seen:
                        self.seen[key] = None
                        yield key
            elif os.path.isfile(item.fspath):
                for key in PyScript(item.fspath):
                    if key not in self.seen:
                        self.seen[key] = None
                        yield key
            else:
                import ipdb;ipdb.set_trace()

    def _createchild(self, path):
        return distFromPath(path)


class UnionNode(LazyNode):
    """Returns the union of its backends
    """



class Part(LazyNode):
    """A part of a buildout, having scripts as children
    """


class Buildout(FSNode):
    """A buildout project

    Parts are children, the rest is attributes
    """
    def _iterchildkeys(self):
        """Return the iterator over part names
        """

    def _createchild(self, key):
        """Return a Part node for key
        """



class DistributionCmd(Cmd):
    """A command used to handle distributions
    """
    def _initialize(self):
        """Initialization, for example self.cfg.setdefault(.., ..)
        """
        self.cfg.setdefault('scripts_dir', 'bin')
        self.dists = ScriptDirectory(self.cfg['scripts_dir'])


class List(Cmd):
    """List distributions, by default all distributions used by the current
    environment.
    """
    def _initialize(self):
        """Initialization, for example self.cfg.setdefault(.., ..)
        """

    def __call__(self, pargs=None):
        """So far we just list all distributions used by the current env
        """
        dists = [x for x in PyScriptDir(os.path.join(self.root, 'bin'))]
        return dists

    def init_argparser(self, parser):
        """Add our arguments to a parser.
        """


class Clone(Cmd):
    """Clone a distribution, binary to eggs-mrsd/, source to src-mrsd/.

    XXX:
        mrsd clone -> list dists available for cloning bdist and sdist
        mrsd clone foo -> clone bdist if exists, otherwise sdist

        For now, just bdist support
    """
    def _initialize(self):
        """Initialization, for example self.cfg.setdefault(.., ..)
        """

    def __call__(self, pargs=None):
        """Execute the command, will receive parser args from argparse, when
        run from cmdline.
        """

    def init_argparser(self, parser):
        """Add our arguments to a parser.
        """



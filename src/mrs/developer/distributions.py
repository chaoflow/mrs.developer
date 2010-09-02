from mrs.developer.node import File
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
        

class PyScript(LazyNode):
    """A channel that returns distributions used by a python script
    """
    def _iterchildkeys(self):
        """Our keys are the paths to distributions used by our script
        """
        consume = False
        for line in File(path):
            line = line.strip()
            if line.startswith('sys.path[0:0] = ['):
                consume = True
            elif line == ']':
                break
            elif not consume:
                continue
            # The key is the full path to the distribution
            key = line[2:-2]
            if not key.endswith('.egg'):
                logger.warn("Ignoring yet unsupported distribution in '%s'.")
                continue
            elif not os.path.isdir(key):
                logger.warn("Ignoring yet unsupported zipped bdist in '%s'.")
                continue
            yield key

    def _createchild(self, path):
        return distFromPath(path)


class PyScriptDir(Node):
    """A channel for all distributions from python scripts in a file
    """
    def _iterchildkeys(self):
        for item in Directory(self.path):
            if os.path.isdir(item.path):
                for key in PyScriptDir(item.path):
                    yield key
            elif os.path.isfile(item.path):
                for dist in PyScript(item.path):
                    yield dist


class UnionNode(Node):
    """Returns the union of its backends
    """



class Part(Node):
    """A part of a buildout, having scripts as children
    """


class Buildout(Node):
    """A buildout projecto

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
        dists = []
        return 

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



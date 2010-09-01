from mrs.developer.node import 

class Distribution(object):
    """A distribution
    """
    url = None
    

class SDist(Distribution):
    """A source distribution
    """


class BDist(Distribution):
    """A binary distribution
    """


class Channel(object):
    """A channel for something
    """
    def __init__(self, name, parent=None):
        self.__name__ = name
        self.__parent__ = parent


class PyScript(Node):
    """A channel that returns distributions used by a python script
    """
    def _load_keys(self):
        """Our keys are the paths to distributions used by the script our name
        points to.
        """
        consume = False
        for line in fileiter(self.__name__):
            line = line.strip()
            if line.startswith('sys.path[0:0] = ['):
                consume = True
            elif line == ']':
                break
            elif not consume:
                continue
            key = line[2:-2]
            try:
                self._keys[key]
            except KeyError:
                self._keys[key] = None

    def __getitem__(self, key):
        """Return channel/distribution for key

        A key can be
        - a string ending in .egg, path to a bdist
        - path to a directory

        XXX: This does not belong into PyScript
        """
            
            
class Buildout(Node):
    """A channel that provides access to a buildout project.
    """
    def 
            

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



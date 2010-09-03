import os
import shutil

from subprocess import check_call

from mrs.developer.base import Cmd
from mrs.developer.base import logger
from mrs.developer.node import Directory
from mrs.developer.node import File
from mrs.developer.node import FSNode
from mrs.developer.node import LazyNode



class Distribution(FSNode):
    """A distribution
    """


class SDist(Distribution):
    """A source distribution
    """


class BDist(Distribution):
    """A binary distribution
    """

class BDistDirectory(Directory):
    """A directory containing binary distributions
    """
    def _createchild(self, key):
        return BDist(key)


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
    head, tail = os.path.split(path)
    parent = BDistDirectory(head)
    dist = parent[tail]
    return dist


class PyScript(FSNode):
    """A channel that returns distributions used by a python script
    """
    def _iterchildkeys(self):
        """Our keys are the paths to distributions used by our script
        """
        consume = False
        for line in File(self.abspath):
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
    # We are not real parents, the folders where the dists really live are
    adopting = False

    def _iterchildkeys(self):
        self.seen = {}
        for item in Directory(self.abspath).values():
            if os.path.isdir(item.abspath):
                for key in PyScriptDir(item.abspath):
                    if key not in self.seen:
                        self.seen[key] = None
                        yield key
            elif os.path.isfile(item.abspath):
                for key in PyScript(item.abspath):
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


class List(Cmd):
    """List distributions, by default all distributions used by the current
    environment.
    """
    def init_argparser(self, parser):
        """Add our arguments to a parser.
        """
        parser.add_argument(
                'channel',
                nargs='*',
                help='Distributions to clone, can be a single distribution.',
                )

    def __call__(self, channels=None, pargs=None):
        """So far we just list all distributions used by the current env
        """
        if not os.path.isdir(os.path.join(self.root, 'eggs-mrsd')):
            os.mkdir(os.path.join(self.root, 'eggs-mrsd'))
        if not self.root:
            logger.error("Not rooted, run 'mrsd init'.")
            return
        if channels is None:
            if pargs is not None:
                channels = pargs.channel
        if type(channels) not in (tuple, list):
            channels = (channels,)
        for channel in channels:
            if channel == "cloned":
                cloned = Directory(os.path.join(self.root, 'eggs-mrsd'))
                return [x.abspath for x in cloned.values()]

        pyscriptdir = PyScriptDir(os.path.join(self.root, 'bin'))
        return dict((x.__name__, x.abspath) for x in pyscriptdir.values())


def copy(dist, dir_):
    """copies a binary distribution to a directory
    """
    head, tail = os.path.split(dist.abspath)
    target = BDist(os.path.join(dir_.abspath, tail))
    shutil.copytree(
            dist.abspath,
            target.abspath,
            symlinks=True,
            )
    return target


class Clone(Cmd):
    """Clone a distribution, binary to eggs-mrsd/, source to src-mrsd/.

    XXX:
        mrsd clone -> list dists available for cloning bdist and sdist
        mrsd clone foo -> clone bdist if exists, otherwise sdist

        For now, just bdist support
    """
    def init_argparser(self, parser):
        """Add our arguments to a parser.
        """
        parser.add_argument(
                'dist',
                nargs='*',
                help='Distributions to clone. If None will list all '
                     'distributions used by the local env, the local channel.',
                )

    def __call__(self, dists=None, pargs=None):
        """Execute the command, will receive parser args from argparse, when
        run from cmdline.
        """
        if not self.root:
            logger.error("Not rooted, run 'mrsd init'.")
            return
        if dists is None:
            dists = pargs.dist
            if not dists:
                return self.cmds.list()
        if type(dists) not in (tuple, list):
            dists = (dists,)
        for dist in dists:
            self._clone(dist)

    def _clone(self, dist):
        # find the distribution
        pyscriptdir = PyScriptDir(os.path.join(self.root, 'bin'))
        if not os.path.isabs(dist):
            source = pyscriptdir[os.path.abspath(dist)]
        else:
            source = pyscriptdir[dist]
        target = copy(source, Directory(os.path.join(self.root, 'eggs-mrsd')))
        # initialize as a git repo and create initial commit
        check_call(['git', 'init'], cwd=target.abspath)
        check_call(['git', 'add', '.'], cwd=target.abspath)
        check_call(['git', 'commit', '-m', 'initial from: %s' % (source.abspath,)],
                cwd=target.abspath)
        check_call(['git', 'tag', 'initial'], cwd=target.abspath)


class Patch(Cmd):
    """Patch management, list, generate and apply patches on bdist eggs.
    """
    def _initialize(self):
        # read a list of available patches
        patches_dir = self.cfg.setdefault('patches_dir', 'eggs-patches')
        patches_dir = os.path.join(
                self.root or os.curdir,
                patches_dir,
                )
        if not os.path.isdir(patches_dir):
            os.mkdir(patches_dir)
        for pkg in os.listdir(patches_dir):
            self.patches[pkg] = []
            pkg_patch_dir = os.path.join(patches_dir, pkg)
            for patch in os.listdir(pkg_patch_dir):
                patch = os.path.abspath(patch)
                self.patches[pkg].append(patch)

    def init_argparser(self, parser):
        """Add our arguments to a parser
        """
        actions = parser.add_mutually_exclusive_group()
        actions.add_argument(
                '--list',
                dest='action',
                action='store_const',
                const=self.list,
                help=self.list.__doc__,
                )
        actions.add_argument(
                '--generate',
                dest='action',
                action='store_const',
                const=self.generate,
                help=self.generate.__doc__,
                )
        actions.add_argument(
                '--apply',
                dest='action',
                action='store_const',
                const=self.apply,
                help=self.apply.__doc__,
                )
        parser.set_defaults(action=self.list)
        parser.add_argument(
                'dist',
                nargs='*',
                help='Eggspace to customize.',
                )

    def list(self):
        """List patches.
        """
        return self.patches

    def generate(self, namespace):
        """Generate patches from customized bdists.
        """
        check_call(['git', 'add', '.'], cwd=target.abspath)

    def apply(self):
        """Apply patches.
        """

    def __call__(self, pargs=None):
#        for egg in eggspace if egg in self.patches:
#            self._customize(egg)
#            self._patch(egg, self.patches[egg.name])
        pass

    def _patch(self, egg, patches):
        """Apply patches to egg
        """
        for patch in patches:
            patch(egg)

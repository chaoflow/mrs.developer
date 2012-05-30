import os
import shutil
import subprocess

from subprocess import check_call
from subprocess import Popen, PIPE

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
        if not self.root:
            logger.error("Not rooted, run 'mrsd init'.")
            return
        if not os.path.isdir(os.path.join(self.root, 'eggs-mrsd')):
            os.mkdir(os.path.join(self.root, 'eggs-mrsd'))
        if channels is None:
            if pargs is not None:
                channels = pargs.channel
        if type(channels) not in (tuple, list):
            channels = (channels,)
        for channel in channels:
            if channel == "cloned":
                cloned = Directory(os.path.join(self.root, 'eggs-mrsd'))
                return dict((x.__name__, x.abspath) for x in cloned.values())

        pyscriptdir = PyScriptDir(os.path.join(self.root, 'bin'))
        return dict((x.__name__, x.abspath) for x in pyscriptdir.values())


def copy(dist, targetdir):
    """copies a binary distribution to a directory
    """
    head, tail = os.path.split(dist.abspath)
    target = BDist(os.path.join(targetdir.abspath, tail))
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

    def _clone(self, name):
        """clone a distribution

        name can be:
        - odict-1.3.2-py2.6.egg
        - /home/cfl/.cache/buildout/eggs/odict-1.3.2-py2.6.egg
        - relative path
        """
        dists = self.cmds.list()
        try:
            abspath = dists[name]
        except KeyError:
            # not a name of distribution, might relative or absolute path
            if os.path.isabs(name):
                abspath = name
            else:
                abspath = os.path.abspath(name)
        source = distFromPath(abspath)
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
        self.cfg.setdefault('patches_dir', 'eggs-patches')

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
        return [x for x in Directory(self.patches_dir)]

    def generate(self):
        """Generate patches from customized bdists.

        Limitations for now: one patchset per bdist, only apply to bdist with
        the same name.
        """
        for name, abspath in self.cmds.list('cloned').items():
            # create dir for bdist in patches if not exists
            patches_dir = self.cfg['patches_dir']
            if not os.path.isabs(patches_dir):
                patches_dir = os.path.join(self.root, patches_dir)
            targetdir = os.path.join(patches_dir, name)
            if not os.path.isdir(patches_dir):
                os.mkdir(patches_dir)
            if not os.path.isdir(targetdir):
                os.mkdir(targetdir)
            # format-patch there
            if Popen(['git', 'status', '--porcelain'],
                    stdout=PIPE, cwd=abspath).communicate()[0]:
                logger.warn('Ignoring egg with uncommitted changes: %s.' %
                        (abspath,))
                continue
            tmp = Popen(['git', 'branch', '--no-color'], cwd=abspath,
                    stdout=PIPE).communicate()[0].split('\n')
            currentbranch = None
            for x in tmp:
                if x.startswith('*'):
                    currentbranch = x.split()[1]
                    break
            else:
                raise CouldNotDetectCurrentBranch
            if currentbranch == '__mrsd_patched__': 
                logger.error('Ignoring egg on __mrsd_patched__ branch: %s.' %
                        (abspath,))
                return
            check_call(['git', 'format-patch', '-o', targetdir, 'initial..HEAD'], cwd=abspath)

    def apply(self):
        """Apply patches.

        clone base version
        apply patches
        """
        for patchdir in Directory(self.patches_dir).values():
            try:
                self.cmds.clone(patchdir.__name__)
            except OSError:
                pass
            eggdir = os.path.join(self.root, 'eggs-mrsd', patchdir.__name__)
            try:
                check_call(['git', 'checkout', '-b', '__mrsd_patched__',
                    'initial'], cwd=eggdir)
            except subprocess.CalledProcessError:
                check_call(['git', 'checkout', 'master'], cwd=eggdir)
                check_call(['git', 'branch', '-D', '__mrsd_patched__'], cwd=eggdir)
                check_call(['git', 'checkout', '-b', '__mrsd_patched__',
                    'initial'], cwd=eggdir)
            for patch in patchdir.values():
                check_call(['git', 'am', patch.abspath], cwd=eggdir)

    def __call__(self, pargs=None):
        if self.root is None:
            raise NeedToBeRooted
        patches_dir = self.cfg['patches_dir']
        self.patches_dir = patches_dir = os.path.join(
                self.root,
                patches_dir,
                )
        if not os.path.isdir(patches_dir):
            os.mkdir(patches_dir)
        return pargs.action()

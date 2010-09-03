#!/usr/bin/env python

import os
import shutil
from subprocess import PIPE
from subprocess import Popen
try:
    import json
except ImportError:
    import simplejson as json

from odict import odict
from pkg_resources import iter_entry_points

from mrs.developer.base import Cmd
from mrs.developer.base import CmdWrapper
from mrs.developer.base import check_call
from mrs.developer.base import logger

import mrs.developer.distributions

DEFAULT_CFG_FILE = '.mrsd'


class Init(Cmd):
    """Create a default configuration in the current directory.

    This defines a mrsd root, commands in the subtree will find and use it.
    """
    def __call__(self, path=None, pargs=None):
        cfg_file = os.path.abspath(DEFAULT_CFG_FILE)
        reinit = os.path.isfile(cfg_file)
        self.cmds.save_config(cfg_file)
        if reinit:
            logger.info(u"Reinitialized mrsd root at %s." % \
                    (os.path.abspath(os.curdir)))
        else:
            logger.info(u"Initialized mrsd root at %s." % \
                    (os.path.abspath(os.curdir)))


class HookCmd(Cmd):
    start_indicator = '\n### mrs.developer'
    stop_indicator = '### mrs.developer: end.\n'

    def _initialize(self):
        self.cfg.setdefault('scripts_dir', 'bin')

    def __call__(self, pargs=None):
        """If no arguments are specified, we hook into all known scripts

        except buildout and mrsd
        """
        scriptdir = os.path.join(
                self.root or os.curdir,
                self.cfg['scripts_dir']
                )
        for name in os.listdir(scriptdir):
            script = os.path.join(scriptdir, name)
            if name in ('buildout', 'mrsd'):
                logger.debug("Ignoring %s." % (script,))
                continue
            if name[0] == '.':
                logger.debug("Ignoring %s." % (script,))
                continue
            # Will be either hookin or hookout
            self._cmd(script)


class Hookin(HookCmd):
    """Hook into a script's sys.path generation, renew if hooked already.
    """
    start_str = 'sys.path[0:0] = ['

    hook = \
"""%s: inject our paths upfront
try:
    import json
except ImportError:
    import simplejson as json
from subprocess import Popen, PIPE

mrsdpaths = Popen(
       ["mrsd", "list", "cloned"],
       stdout=PIPE,
       ).communicate()[0]
if mrsdpaths:
    sys.path[0:0] = json.loads(mrsdpaths).values()
%s"""

    def _hookin(self, script):
        """This command will be called by HookCmd.__call__
        """
        f = open(script, 'r')
        content = f.read()
        f.close()
        if self.start_indicator in content:
            self.cmds.hookout()
            f = open(script, 'r')
            content = f.read()
            f.close()
        if self.start_str not in content:
            logger.debug("Not hooking into %s." % (script,))
            return
        idx = content.find(self.start_str) + len(self.start_str)
        idx = content.find(']', idx)+2
        hooked = content[:idx]
        hooked += self.hook % \
                (self.start_indicator, self.stop_indicator)
        hooked += content[idx:]
        f = open(script, 'w')
        f.write(hooked)
        f.close()
        logger.info("Hooked in: %s." % (script,))

    _cmd = _hookin


class Hookout(HookCmd):
    """Remove our hook from scripts.
    """
    def _hookout(self, script):
        """This command will be called by HookCmd.__call__
        """
        f = open(script, 'r')
        content = f.read()
        f.close()
        if not self.start_indicator in content:
            return
        start = content.find(self.start_indicator)
        stop = content.rfind(self.stop_indicator) + len(self.stop_indicator)
        content = content[:start] + content[stop:]
        f = open(script, 'w')
        f.write(content)
        f.close()
        logger.info("Hooked out: %s." % (script,))

    _cmd = _hookout


class Patch(Cmd):
    """Patch management, list, generate and apply patches on bdist eggs.
    """
    def _initialize(self):
        # read a list of available patches
        patches_dir = self.cfg['patches_dir'].setdefault('eggs-patches')
        patches_dir = os.path.join(
                self.root or os.curdir,
                patches_dir,
                )
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
        action.add_argument(
                '--list',
                dest='action',
                action='store_const',
                const=self.list,
                help=self.list.__doc__,
                default=True,
                )
        action.add_argument(
                '--generate',
                dest='action',
                action='store_const',
                const=self.generate,
                help=self.list.__doc__,
                default=True,
                )
        action.add_argument(
                'eggspace',
                nargs='*',
                help='Eggspace to customize.',
                )

    def list(self, namespace):
        """List patches for namespace.
        """
        return self.patches

    def generate(self, namespace):
        """Generate patches from customized bdist eggs.
        """

    def apply(self, namespace):
        """Apply patches for namespace.
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


class Test(CmdWrapper):
    """Run the tests, from anywhere in your project, without the need to know
    where your testrunner lives.
    """
    cmdline = ["./bin/test"]


class Run(CmdWrapper):
    """Run scripts from ``bin/`` from anywhere in your project.
    """
    def _cmdline(self, args):
        cmd = args.pop(0)
        cmd = os.path.join('.', 'bin/', cmd)
        return [cmd] + args


class CmdSet(object):
    """The mrsd command set.
    """

    entry_point_keys = {
        'commands': 'mrs.developer.commands',
        'aliases': 'mrs.developer.aliases'
    }

    @property
    def root(self):
        try:
            return os.path.dirname(self.cfg_file)
        except AttributeError:
            return None

    def __init__(self):
        self.cfg = dict()
        self.cfg_file = None
        self.cmds = odict()
        self.aliases = {}
        for ep in iter_entry_points(self.entry_point_keys['commands']):
            self.cmds[ep.name] = ep.load()(ep.name, self)
        for ep in iter_entry_points(self.entry_point_keys['aliases']):
            self.aliases[ep.name] = ep.load()()

    def __getattr__(self, name):
        try:
            cmds = object.__getattribute__(self, 'cmds')
        except AttributeError:
            return object.__getattribute__(self, name)
        if name in cmds:
            return cmds[name]

    def __getitem__(self, name):
        return self.cmds[name]

    def __iter__(self):
        return self.cmds.__iter__()

    def iteritems(self):
        return self.cmds.iteritems()

    def load_config(self, cfg_file=DEFAULT_CFG_FILE):
        """Load config from curdir or parents
        """
        cfg_file = os.path.abspath(cfg_file)
        try:
            logger.debug("Trying to load config from %s." % (cfg_file,))
            f = open(cfg_file)
        except IOError:
            # check in parent dir
            head, tail = os.path.split(cfg_file)
            pardir = os.path.dirname(head)
            if head == pardir:
                raise RuntimeError("Found no configuration to load.")
            cfg_file = os.path.join(pardir, tail)
            self.load_config(cfg_file)
        else:
            logger.debug("Loaded config from %s." % (cfg_file,))
            self.cfg = json.load(f)
            self.cfg_file = cfg_file
            f.close()

    def save_config(self, cfg_file=None):
        cfg_file = cfg_file or self.cfg_file
        cfg_file = os.path.abspath(cfg_file)
        f = open(cfg_file, 'w')
        json.dump(self.cfg, f, indent=4)
        f.close()
        logger.debug("Wrote config to %s." % (cfg_file,))

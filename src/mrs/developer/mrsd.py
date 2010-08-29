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

from mrs.developer.base import Cmd
from mrs.developer.base import check_call
from mrs.developer.base import logger
from mrs.developer.develop import Checkout
from mrs.developer.develop import Develop

DEFAULT_CFG_FILE = '.mrsd'


class Stock(Cmd):
    """Return dictionary of stock eggs.

    Format: stock = { namespace = { egg_name = egg_source } }.
    Namespace for now is the relative paths to the script the egg reference was
    found in.
    """
    def __call__(self, pargs=None):
        """Dump all known eggs
        """
        scriptdir = os.path.join(
                self.root or os.curdir,
                self.cfg['scripts_dir']
                )
        stock = dict()
        paths = set()
        for script in [x for x in os.listdir(scriptdir) if not x[0] == '.']:
            scriptpath = os.path.join(scriptdir, script)
            f = open(scriptpath)
            paths = self._paths(f.read())
            f.close()
            eggspace = stock[scriptpath] = dict()
            for path in paths:
                if not path.endswith('.egg'):
                    continue
                name = path.split(os.path.sep)[-1].split('-')[0]
                eggspace[name] = path
        return stock

    def _paths(self, script):
        start_str = 'sys.path[0:0] = ['
        start = script.find(start_str) + len(start_str)
        end = script.find(']', start)
        return [x.split("'")[1] for x in script[start:end].split()]


class Customize(Cmd):
    """Create a copy of a stock egg inside the custom_eggs_dir.

    Will be set up as git repo.

    Understood eggspaces are: name of an egg, patched (eggs we have patches for).
    """
    def _initialize(self):
        # cfg defaults
        self.cfg.setdefault('custom_eggs_dir', 'eggs-mrsd')

    def __call__(self, egg_names=None, pargs=None):
        if pargs is not None:
            egg_names = pargs.egg_name
        custom_eggs_dir = os.path.join(
                self.root or os.path.curdir,
                self.cfg['custom_eggs_dir'],
                )
        eggspaces = self.parent.stock()
        if not isinstance(egg_names, list):
            egg_names = [egg_names]
        for egg_name in egg_names:
            for name, eggspace in eggspaces.iteritems():
                try:
                    stock_path = eggspace[egg_name]
                except KeyError:
                    continue
                else:
                    break
            else:
                raise ValueError(u"Egg %s not in stock" % (egg_name,))
            custom_path = os.path.join(custom_eggs_dir, egg_name)
            # create the parent directory
            if not os.path.isdir(custom_eggs_dir):
                os.mkdir(custom_eggs_dir)
            # copy the stock egg to customized eggs
            shutil.copytree(stock_path, custom_path, symlinks=True)
            # initialize as a git repo and create initial commit
            check_call(['git', 'init'], cwd=custom_path)
            check_call(['git', 'add', '.'], cwd=custom_path)
            check_call(['git', 'commit', '-m', 'initial from: %s' % (stock_path,)],
                    cwd=custom_path)
            check_call(['git', 'tag', 'initial'], cwd=custom_path)

    def init_argparser(self, parser):
        """Add our arguments to a parser
        """
        parser.add_argument(
                'eggspace',
                nargs='+',
                help='Eggspace to customize.',
                )


class Paths(Cmd):
    """Return the paths to be injected into a script's sys.path.
    """
    def __call__(self, pargs=None):
        """script is the (relative) path to the script
        """
        custom_eggs_dir = os.path.join(
                self.root or os.curdir,
                self.cfg['custom_eggs_dir']
                )
        # dir may not exist
        if os.path.exists(custom_eggs_dir):
            # For now we return one list for all
            paths = [os.path.join(custom_eggs_dir, x)
                     for x in os.listdir(custom_eggs_dir)]
            return paths
        else:
            return []


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
            # Will be either hookin or unhook
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

paths = Popen(
       ["mrsd", "paths"],
       stdout=PIPE,
       ).communicate()[0]
if paths:
    sys.path[0:0] = json.loads(paths)
%s"""

    def _hookin(self, script):
        """This command will be called by HookCmd.__call__
        """
        f = open(script, 'r')
        content = f.read()
        f.close()
        if self.start_indicator in content:
            self.parent.cmds['unhook']()
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
        logger.info("Hooked into %s." % (script,))

    _cmd = _hookin


class Unhook(HookCmd):
    """Remove our hook from scripts.
    """
    def _unhook(self, script):
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
        logger.info("Unhooked %s." % (script,))

    _cmd = _unhook


class Init(Cmd):
    """Create a default configuration in the current directory.

    This defines a mrsd root, commands in the subtree will find and use it.
    """
    def __call__(self, path=None, pargs=None):
        cfg_file = os.path.abspath(DEFAULT_CFG_FILE)
        reinit = os.path.isfile(cfg_file)
        self.parent.save_config(cfg_file)
        if reinit:
            logger.info(u"Reinitialized mrsd root at %s." % \
                    (os.path.abspath(os.curdir)))
        else:
            logger.info(u"Initialized mrsd root at %s." % \
                    (os.path.abspath(os.curdir)))


class CmdSet(object):
    """The mrsd command set.
    """
    @property
    def root(self):
        try:
            return os.path.dirname(self.cfg_file)
        except AttributeError:
            return None

    def __init__(self):
        self.cfg = dict()
        self.cfg_file = None
        self.cmds = odict([
                ('init', Init('init', self)),
                ('stock', Stock('stock', self)),
                ('customize', Customize('customize', self)),
                ('paths', Paths('paths', self)),
                ('hookin', Hookin('hookin', self)),
                ('unhook', Unhook('unhook', self)),
                ('develop', Develop('develop', self)),
                ('checkout', Checkout('checkout', self)),
                ])

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
            parent = os.path.dirname(head)
            if head == parent:
                raise RuntimeError("Found no configuration to load.")
            cfg_file = os.path.join(parent, tail)
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

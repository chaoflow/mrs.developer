#!/usr/bin/env python

import os
try:
    import json
except ImportError:
    import simplejson as json

from mrs.developer.base import Cmd
from mrs.developer.develop import Checkout
from mrs.developer.develop import Develop

DEFAULT_CFG_FILE = '.mrsd'


class Stock(Cmd):
    """Return dictionary of stock eggs.
    """
    def __call__(self, egg_name=None):
        """If no args, return dict of all eggs in stock
        """
        paths = set()
        for script in [x for x in os.listdir('./bin') if not x[0] == '.']:
            f = open('./bin/' + script)
            paths.update(self._paths(f.read()))
            f.close()
        stock = dict()
        for path in paths:
            if not path.endswith('.egg'):
                continue
            name = path.split(os.path.sep)[-1].split('-')[0]
            stock[name] = path
        if egg_name:
            return stock[egg_name]
        else:
            return stock

    def _paths(self, script):
        start_str = 'sys.path[0:0] = ['
        start = script.find(start_str) + len(start_str)
        end = script.find(']', start)
        return [x.split("'")[1] for x in script[start:end].split()]


class Customize(Cmd):
    """Create a copy of a stock egg inside the custom_eggs_dir.

    Will be set up as git repo.
    """
    def _initialize(self):
        # cfg defaults
        cfg = self.cfg
        cfg.setdefault('custom_eggs_dir', 'eggs-customized')
        # create the parent directory
        if not os.path.isdir(cfg['custom_eggs_dir']):
            os.mkdir(cfg['custom_eggs_dir'])

    def __call__(self, egg_name):
        stock_path = self.parent.cmds['stock'](egg_name)
        custom_path = os.path.join(self.cfg['custom_eggs_dir'], egg_name)
        # copy the stock egg to customized eggs
        shutil.copytree(stock_path, custom_path, symlinks=True)
        # initialize as a git repo and create initial commit
        check_call(['git', 'init'],
                cwd=custom_path, stdout=PIPE, stderr=PIPE)
        check_call(['git', 'add', '.'],
                cwd=custom_path, stdout=PIPE, stderr=PIPE)
        check_call(['git', 'commit', '-m', 'initial from: %s' % (stock_path,)],
                cwd=custom_path, stdout=PIPE, stderr=PIPE)
        check_call(['git', 'tag', 'initial'],
                cwd=custom_path, stdout=PIPE, stderr=PIPE)

    def init_argparser(self, parser):
        """Add our arguments to a parser
        """
        parser.add_argument(
                'egg_name',
                nargs='+',
                help='Name of the egg to copy to %s for customization.' % \
                            (os.path.join('.', self.cfg['custom_eggs_dir'],)),
                )


class Paths(Cmd):
    """Return the paths to be injected into a script's sys.path.
    """
    def __call__(self, script=None):
        """script is the (relative) path to the script
        """
        # For now we return one list for all
        paths = [os.path.abspath(os.path.join(self.cfg['custom_eggs_dir'], x)) \
                for x in os.listdir(self.cfg['custom_eggs_dir'])]
        return paths


class HookCmd(Cmd):
    start_indicator = '\n### mrs.developer'
    stop_indicator = '### mrs.developer: end.\n'

    def __call__(self):
        """If no arguments are specified, we hook into all known scripts

        except buildout and mrsd
        """
        for name in os.listdir('./bin'):
            if name in ('buildout', 'mrsd'):
                continue
            if name[0] == '.':
                continue
            # Will be either hookin or unhook
            self._cmd('./bin/' + name)


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
        idx = content.find(self.start_str) + len(self.start_str)
        idx = content.find(']', idx)+2
        hooked = content[:idx]
        hooked += self.hook % \
                (self.start_indicator, self.stop_indicator)
        hooked += content[idx:]
        f = open(script, 'w')
        f.write(hooked)
        f.close()

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

    _cmd = _unhook


class CmdSet(object):
    """The mrsd command set.
    """
    def __init__(self, cfg_file=DEFAULT_CFG_FILE):
        self.cfg_file = cfg_file
        try:
            f = open(cfg_file)
        except IOError:
            self.cfg = dict()
        else:
            self.cfg = json.load(f)
            f.close()

        self.cmds = dict(
                stock=Stock('stock', self),
                customize=Customize('customize', self),
                paths=Paths('paths', self),
                unhook=Unhook('unhook', self),
                hookin=Hookin('hookin', self),
                develop=Develop('develop', self),
                checkout=Checkout('checkout', self),
                )

    def save_config(self, cfg_file=None):
        cfg_file = cfg_file or self.cfg_file
        f = open(cfg_file, 'w')
        json.dump(self.cfg, f, indent=4)
        f.close()

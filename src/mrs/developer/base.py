import sys

from subprocess import check_call as real_check_call
from subprocess import call as real_call

import logging
logger = logging.getLogger("mrsd")


def check_call(*args, **kws):
    """wrap subprocess.check_call for logging
    """
    logger.info("Running: %s with %s" % (args, kws))
    real_check_call(*args, **kws)


def call(*args, **kws):
    """wrap subprocess.call for logging
    """
    logger.info("Running: %s with %s" % (args, kws))
    real_call(*args, **kws)


class Cmd(object):
    """An abstract command

    I might be beneficial for subcommands to implement __call__, init_argparser
    and _initialize.
    """
    @property
    def cfg(self):
        return self.__parent__.cfg

    @property
    def root(self):
        return self.__parent__.root

    @property
    def cmds(self):
        return self.__parent__

    def __init__(self, name, parent):
        self.__name__ = name
        self.__parent__ = parent
        self._initialize()

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


class CmdWrapper(Cmd):
    """An abstract cmd that just wraps another cmdline tool.

    Subclasses need to override ``cmdline``, it will be run in the mrsd root.
    """
    cmdline = []

    def __call__(self, args=None, pargs=None):
        # we ignore pargs
        if args is None:
            args = sys.argv[2:]
        call(self._cmdline(args), cwd=self.root)

    def _cmdline(self, args):
        return self.cmdline + args

    def init_argparser(self, parser):
        """Add our arguments to a parser

        XXX: Enable a -h / --help of the wrapped command, eg. --wrapped-help
        """
        parser.add_argument(
                'args',
                nargs='*',
                help='Arguments to pass to %s.' % (self.cmdline,),
                )


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

    subclasses need to implement __call__ and may implement _initialize
    """
    @property
    def cfg(self):
        return self.parent.cfg

    @property
    def root(self):
        return self.parent.root

    def __init__(self, name, parent):
        self.__name__ = name
        self.parent = parent
        try:
            self._initialize()
        except AttributeError:
            pass

    def init_argparser(self, parser):
        pass


class CmdWrapper(Cmd):
    """An abstract cmd that just wraps another cmdline tool.

    Subclasses need to override ``cmdline``, it will be run in the mrsd root.
    """
    cmdline = []

    def __call__(self, args=None, pargs=None):
        # we ignore pargs
        if args is None:
            args = sys.argv[2:]
        call(self.cmdline + args, cwd=self.root)

    def init_argparser(self, parser):
        """Add our arguments to a parser

        XXX: Enable a -h / --help of the wrapped command, eg. --wrapped-help
        """
        parser.add_argument(
                'args',
                nargs='*',
                help='Arguments to pass to %s.' % (self.cmdline,),
                )


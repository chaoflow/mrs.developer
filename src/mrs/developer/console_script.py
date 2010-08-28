#!/usr/bin/env python

import argparse
try:
    import json
except ImportError:
    import simplejson as json

from mrs.developer.base import logging, logger
from mrs.developer.mrsd import CmdSet


class ConsoleScript(CmdSet):
    """The console script for the commandset
    """
    name = "mrsd"

    def __call__(self):
        parser = argparse.ArgumentParser(
                prog=self.name,
                formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                )
        parser.add_argument(
                '-d', '--debug',
                dest='debug',
                action='store_true',
                default=False,
                help="Enable debugging output.",
                )
        subparsers = parser.add_subparsers(help='cmd --help')
        for name, cmd in self.iteritems():
            cmd_parser = subparsers.add_parser(
                    name,
                    help=cmd.__doc__,
                    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                    )
            cmd.init_argparser(cmd_parser)
            cmd_parser.set_defaults(cmd=cmd)
        pargs = parser.parse_args()
        if pargs.debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
        logger.debug(u"Rooted at %s." % (self.root,))
        output = pargs.cmd(pargs=pargs)
        if output:
            print json.dumps(output, indent=4, sort_keys=True)


mrsd = ConsoleScript()

if __name__ == "__main__":
    mrsd()

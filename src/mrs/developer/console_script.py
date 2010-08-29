#!/usr/bin/env python

import sys
import argparse
try:
    import json
except ImportError:
    import simplejson as json

from mrs.developer.base import logging, logger
from mrs.developer.base import CmdWrapper
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
            if isinstance(cmd, CmdWrapper):
                cmd_parser.only_known_args = True
        expargs = [sys.argv[0]]
        try:
            expargs.append(self.aliases.get(sys.argv[1], sys.argv[1]))
        except IndexError:
            pass
        else:
            expargs.extend(sys.argv[2:])
        pargs = parser.parse_args(expargs)
        if pargs.debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
        try:
            self.load_config()
        except RuntimeError:
            # we run without a config file
            pass
        if self.root:
            logger.debug(u"Rooted at %s." % (self.root,))
        else:
            logger.debug(u"Running unrooted.")
        output = pargs.cmd(pargs=pargs)
        if output:
            print json.dumps(output, indent=4, sort_keys=True)


mrsd = ConsoleScript()

if __name__ == "__main__":
    mrsd()

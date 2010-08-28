#!/usr/bin/env python

import argparse
try:
    import json
except ImportError:
    import simplejson as json

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
        output = pargs.cmd(pargs=pargs)
        if output:
            print json.dumps(output, indent=4, sort_keys=True)


mrsd = ConsoleScript()

if __name__ == "__main__":
    mrsd()

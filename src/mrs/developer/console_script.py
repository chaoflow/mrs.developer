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
        parser = argparse.ArgumentParser(prog=self.name)
        subparsers = parser.add_subparsers(help='cmd --help')
        for name, cmd in self.cmds.items():
            cmd_parser = subparsers.add_parser(
                    name,
                    help=cmd.__doc__,
                    )
            for kws in cmd.cmdline_args:
                cmd_parser.add_argument(**kws)
            cmd_parser.set_defaults(cmd=cmd)
        pargs = parser.parse_args()
        kws = dict([(arg['dest'], getattr(pargs, arg['dest'])) for arg in pargs.cmd.cmdline_args])
        output = pargs.cmd(**kws)
        if output:
            print json.dumps(output, indent=4)


mrsd = ConsoleScript()

if __name__ == "__main__":
    mrsd()

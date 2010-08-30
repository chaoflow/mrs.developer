import os
import ConfigParser
from xml.etree import ElementTree

from subprocess import check_call
from subprocess import PIPE
from subprocess import Popen

from mrs.developer.base import Cmd
from mrs.developer.base import logger

NAMESPACES = ['default', 'local', 'global']


class Checkout(Cmd):
    """Checkout develop eggs.
    """

    def _initialize(self):
        local_cp = ConfigParser.ConfigParser()
        local_cp.read('sources.cfg')

        self.namespaces = dict(default=dict())
        for namespace, cp in [('local', local_cp),]:
            self.namespaces[namespace] = dict()
            if cp.has_section('sources'):
                for source_name, source_path in cp.items('sources'):
                    self.namespaces[namespace][source_name] = source_path
            if cp.has_option('buildout', 'auto-checkout'):
                for source in cp.get('buildout', 'auto-checkout').split():
                    if source in self.namespaces[namespace]:
                        self.namespaces['default'][source] = \
                                self.namespaces[namespace][source]

    def __call__(self, sourcespaces=None, pargs=None):
        if pargs:
            sourcespaces= pargs.sourcespaces

        if not sourcespaces:
            # TODO: should list all the local sources?
            raise

        srcdir = self.cfg['default_src_dir']
        if not os.path.isdir(srcdir):
            os.mkdir(srcdir)

        if not isinstance(sourcespaces, list):
            sourcespaces = sourcespaces.split()

        for sourcespace in sourcespaces:
            namespace, source = '', ''

            if ':' in sourcespace:
                namespace, source = sourcespace.splir(':')
                if namespace not in self.namespaces.keys():
                    raise Exception('Non existing namespace selected. ("' + \
                                     namespace + '")')
            else:
                if sourcespace in self.namespaces:
                    namespace = sourcespace
                else:
                    source = sourcespace

            if namespace:
                self._sources_for_namespace(source, self.namespaces[namespace])
            elif source:
                for namespace in ['local', 'global']:
                    if namespace in self.namespaces:
                        self._sources_for_namespace(source,
                                                self.namespaces[namespace])

    def _sources_for_namespace(self, source, namespace):
        if source:
            if source in namespace:
                self._run_checkout(source, namespace[source])
            else:
                raise Exception('Wrong source specified: "' + source + '"')
        else:
            for source in namespace:
                self._run_checkout(source, namespace[source])

    def _run_checkout(self, source_name, source):
        srcdir = self.cfg['default_src_dir']
        source_type, source_url = source.split(' ', 1)

        if source_type == 'git':
            check_call(['git', 'clone', source_url, source_name], cwd=srcdir)

        elif source_type == 'git-svn':
            out_, err_ = Popen(['svn', 'log', '--xml',
                source_url.split(' ')[0]],
                stdout=PIPE, stderr=PIPE).communicate()
            first_rev = ElementTree.fromstring(out_).findall(
                'logentry')[-1].get('revision')
            args = ['git', 'svn', 'clone']
            args += source_url.split()
            args += ['-r', '%s:HEAD' % first_rev, source_name]
            check_call(args, cwd=srcdir)

        elif source_type == 'hg':
            check_call(['hg', 'clone', source_url, source_name],
                cwd=srcdir)

        elif source_type == 'svn':
            check_call(['svn', 'checkout', source_url, source_name],
                cwd=srcdir)

        else:
            raise Exception('Wrong type of source (%s!' % source_type)

    def init_argparser(self, parser):
        """Add our arguments to a parser
        """
        parser.add_argument(
                'sourcespaces',
                nargs='+',
                help='List of eggspaces to chekcout. e.g.: '
                     'mrsd checkout <namespace>:',
                )


class Develop(Cmd):
    """Handle develop eggs.
    (fetch develop egg, if not there)

    find scripts that use the egg

    find parts for the scripts

    buildout install these parts
    """
    def _initialize(self):
        self.cfg.setdefault('develop', {})
        self.cfg.setdefault('default_src_dir', 'src-mrsd')

    def __call__(self,
            egg_names=None,
            checkout=True,
            active=True,
            pargs=None,
            ):
        if pargs:
            egg_names = pargs.egg_name
            checkout = pargs.checkout
            active = pargs.active

        if not isinstance(egg_names, list):
            egg_names = [egg_names]

        eggs = dict()
        for name in egg_names:
            if os.path.sep in name:
                path = name
                name = name.split(os.path.sep, name)[-1]
            else:
                path = os.path.join(self.cfg['default_src_dir'], name)
            path = os.path.join(os.path.abspath(os.curdir), path)
            eggs[name] = path

        if checkout:
            Checkout('checkout', self)(egg_names)

        if active:
            for name, path in eggs.iteritems():
                # only activate existing eggs
                if not os.path.isdir(path):
                    logger.warn(
                            'Did not activate %s, path does not exist or '
                            'is not a directory %s.' % (name, path)
                            )
                    continue
                self.cfg['develop'][name] = path
                import pdb; pdb.set_trace()
                check_call([os.path.join('bin', 'buildout'), 'install', ])
        else:
            for name in eggs:
                self.cfg['develop'].pop(name, None)
        self.cmds.save_config()

    def init_argparser(self, parser):
        """Add our arguments to a parser
        """
        parser.add_argument(
                'egg_name',
                nargs='+',
                help='Either (relative) path to development egg or the name '
                    'of the egg directory within %s' % \
                            (os.path.join('.', self.cfg['default_src_dir'],)),
                )
        #parser.add_argument(
        #        '--all',
        #        dest='alleggs',
        #        action='store_true',
        #        default=False,
        #        help='XXX',
        #        )
        checkout = parser.add_mutually_exclusive_group()
        checkout.add_argument(
                '--checkout',
                dest='checkout',
                action='store_true',
                default=True,
                help='Checkout the egg, iff not checked out already.',
                )
        checkout.add_argument(
                '--no-checkout',
                dest='checkout',
                action='store_false',
                default=False,
                help='Do not try to checkout the egg.',
                )
        activate = parser.add_mutually_exclusive_group()
        activate.add_argument(
                '--activate',
                dest='active',
                action='store_true',
                default=True,
                help='Activate the development egg.',
                )
        activate.add_argument(
                '--deactivate',
                dest='active',
                action='store_false',
                default=False,
                help='Deactivate the egg.',
                )



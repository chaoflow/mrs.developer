import ConfigParser
import os
import shutil

from subprocess import check_call
from subprocess import PIPE
from subprocess import Popen

from mrs.developer.base import Cmd


class Checkout(Cmd):
    """Checkout develop eggs.
    """
    def _initialize(self):
        self.cp = ConfigParser.ConfigParser()
        self.cp.read('sources.cfg')

    def __call__(self, egg_names=None, alleggs=False, pargs=None):
        if pargs:
            egg_names = pargs.egg_name
            alleggs = pargs.alleggs

        if egg_names is None and not alleggs:
            raise ValueError(u"Either list eggs or --all is needed.")

        if egg_names is None:
            egg_names = ['collective.vdexvocabulary',
                         'collective.gallery',
                         'collective.uploadify',
                         'whoosh']

        srcdir = self.cfg['default_src_dir']
        if not os.path.isdir(srcdir):
            os.mkdir(srcdir)

        if not isinstance(egg_names, list):
            egg_names = [egg_names]

        for egg_name in egg_names:
            try:
                source_type, source_url = self.cp.get('sources', egg_name).split(' ', 1)
            except ConfigParser.NoOptionError:
                raise Exception('No source found for "' + egg_name + '".')

            if source_type == 'git':
                check_call(['git', 'clone', source_url, egg_name],
                    cwd=srcdir)

            elif source_type == 'git-svn':
                out_, err_ = Popen(['svn', 'log', '--xml',
                    source_url.split(' ')[0]],
                    stdout=PIPE, stderr=PIPE).communicate()
                first_rev = ElementTree.fromstring(out_).findall(
                    'logentry')[-1].get('revision')
                args = ['git', 'svn', 'clone']
                args += source_url.split()
                args += ['-r', '%s:HEAD' % first_rev, egg_name]
                check_call(args, cwd=srcdir)

            elif source_type == 'hg':
                check_call(['hg', 'clone', source_url, egg_name],
                    cwd=srcdir)

            elif source_type == 'svn':
                check_call(['svn', 'checkout', source_url, egg_name],
                    cwd=srcdir)

            else:
                raise Exception('Wrong type of source (%s!' % source_type)

    def init_argparser(self, parser):
        """Add our arguments to a parser
        """
        parser.add_argument(
                'egg_name',
                nargs='*',
                help='Name of the egg to check out as development egg. '
                    'If not specified, --all is needed',
                )
        parser.add_argument(
                '--all',
                dest='alleggs',
                action='store_true',
                default=False,
                help='Checkout all development eggs specified in sources.cfg.',
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
            # do checkout, don't fail if it exists
            pass

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
        else:
            for name in eggs:
                self.cfg['develop'].pop(name, None)
        self.parent.save_config()

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



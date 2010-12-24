from mrs.developer.base import logger
from mrs.developer.distributions import PyScriptDir
from mrs.developer.base import Cmd
import sys
import os

try:
    import pygraphviz as pgv
except ImportError:
    pgv = None


def depth_first_search(graph, vertices, vertex, marked_vertices):
    """This method is used for finding circular dependencies and marking
    them red.
    """
    marked_vertices.append(vertex)
    for target in vertices[vertex]:
        if target not in marked_vertices:
            depth_first_search(graph, vertices, target, marked_vertices)
        elif marked_vertices.index(target) == 0:
            graph.add_edge(vertex, target, color='red', style='bold')


class Graph(Cmd):
    """BROKEN: Create a dependency graph using ``graphviz``.
    """
    if pgv is None:
        __doc__ += 'DISABLED, run ``mrsd graph`` for more information.'

    def init_argparser(self, parser):
        """Add our arguments to a parser
        """

        parser.add_argument(
            '--filename', '-n',
            dest='filename',
            action='store',
            default='graph.pdf',
            help='Filename of the output file')

        parser.add_argument(
            '--dotfile',
            dest='dotfile',
            action='store',
            default=None,
            help='Create a dotfile with this name.')

        mutual = parser.add_mutually_exclusive_group(required=False)

        parser.add_argument(
            '--follow', '-f',
            dest='follow',
            action='store_true',
            default=False,
            help='Add the direct dependencies of develop-dists to the graph.')

        mutual.add_argument(
            '--recursive', '-r',
            dest='recursive',
            action='store_true',
            default=False,
            help='Follow the dependencies of develop-dists recursively.')


    def __call__(self, dists=None, pargs=None):
        if pgv is None:
            print 'ERROR: could not import pygraphviz.'
            print ''
            print 'INSTALLATION:'
            print '- install graphviz: http://www.graphviz.org/'
            print '- install pygraphviz: http://networkx.lanl.gov/pygraphviz/'
            sys.exit(0)

        self.pargs = pargs

        vertices = self.get_dependency_map()

        graph = pgv.AGraph(directed=True, layout='dot', mindist=1, mclimit=10,
                           sep="0.01", outputorder="breadthfirst", rankdir="LR",
                           size="20!", splines=True, fontsize=14,
                           concentrate=False, nodesep="0.25", normalize=False)
        graph.node_attr.update(shape='tab', fontsize=18)
        graph.edge_attr.update(decorate=False)

        # we need to sort the names - we wanna have a static output
        node_names = vertices.keys()
        node_names.sort()

        # create the nodes
        for pkg in node_names:
            graph.add_node(pkg)

        # create the edges
        for pkg in node_names:
            requires = vertices[pkg]
            for name in requires:
                graph.add_edge(pkg, name, color='grey50')

        # now lets mark circular dependencies red. they are evil.
        for pkg in node_names:
            depth_first_search(graph, vertices, pkg, [])

        if len(node_names) > 150:
            logger.warning('Building graph with %i nodes, ' % len(node_names) +\
                               'this may take a while!')

        output_files = []

        # create a dotfile?
        if pargs.dotfile:
            graph.write(pargs.dotfile)
            output_files.append(pargs.dotfile)

        # now - create the output
        graph.draw(pargs.filename, prog='dot')
        output_files.append(pargs.filename)

        return output_files

    def get_dependency_map(self):
        """Build the dependency map - extras are already reduced.
        """

        if not self.root:
            logger.error("Not rooted, run 'mrsd init'.")
            sys.exit(0)

        src_dir = os.path.join(self.root, 'src')
        if not os.path.isdir(src_dir):
            logger.error('Expected %s to be the source directory' % src_dir)
            sys.exit(0)

        # dependencies including extras for each egg
        dependencies = {}

        for name in os.listdir(src_dir):
            path = os.path.join(src_dir, name)

            # is it a dir?
            if not os.path.isdir(path):
                continue

            # does it have a .egg-info?
            egginfos = filter(lambda n: os.path.isdir(os.path.join(path, n)) \
                                  and n.endswith('.egg-info'), os.listdir(path))

            if len(egginfos) > 0:
                pkgname, requires = self._read_egginfo(os.path.join(
                        path, egginfos[0]))
                dependencies[pkgname] = requires

        return self._reduce_extras(dependencies)

    def _reduce_extras(self, dependencies):
        """Reduces extras dependending in the requires of the other dists.
        """

        follow = self.pargs.follow or self.pargs.recursive
        recursive = self.pargs.recursive


        # create data of dependencies without extras ..
        data = dict([(k, v['']) for k, v in dependencies.items()])

        # .. now add the extras
        changed = True
        while changed:
            changed = False
            for pkg in data.keys()[:]:
                deps = data[pkg]
                new_deps = []
                for dep in deps:

                    if '[' in dep:
                        subpkg, extras = dep.split(']', 1)[0].split('[', 1)
                        subpkg = subpkg.strip()
                        extras = [e.strip() for e in extras.split(',')]
                    else:
                        subpkg = dep.strip()
                        extras = []

                    if subpkg not in dependencies and not follow:
                        continue

                    if subpkg not in dependencies:
                        changed = True

                        if recursive:
                            # add package to dependencies map
                            name, requires = self._read_third_party_egginfo(subpkg)
                            if not name:
                                continue
                        else:
                            requires = {'': []}

                        dependencies[subpkg] = requires
                        data[subpkg] = requires['']

                    if extras:
                        changed = True
                        for extra in extras:
                            if extra not in dependencies[subpkg]:
                                continue

                            data[subpkg] = list(set(
                                    data[subpkg] + dependencies[subpkg][extra]))

                    new_deps.append(subpkg)

                if set(deps) != set(new_deps):
                    changed = True
                    data[pkg] = new_deps

        return data

    def _read_egginfo(self, egginfo_dir):
        """Reads the egginfo_dir
        """

        name = None
        requires = {'': []}

        # read the name of the egg
        pkg_info = open(os.path.join(egginfo_dir, 'PKG-INFO')).read()
        pkgname = filter(lambda row: row.startswith('Name: '),
                         pkg_info.split('\n'))[0].split(': ',1)[1].strip()
        name = pkgname

        # read requires.txt
        requires_file = os.path.join(egginfo_dir, 'requires.txt')
        if os.path.isfile(requires_file):
            rows = open(requires_file).read().strip().split('\n')
            current_extra = ''

            for row in rows:
                row = row.strip()

                if row and row.startswith('['):
                    current_extra = row[1:-1]
                    requires[current_extra] = []

                elif row:
                    requires[current_extra].append(row.split(
                            '>', 1)[0].split(
                            '=', 1)[0].split(
                            '<', 1)[0].strip().replace(' ', ''))

        return name, requires

    def _read_third_party_egginfo(self, pkgname):
        """Reads and returns the egg-info of a third party packge. Returns
        (None, None) if the package could not be found. Used when running
        with --recursive.
        """

        if '_third_party_requires' not in dir(self):
            self._third_party_requires = {}

            psd = PyScriptDir(os.path.join(self.root, 'bin'))
            for path in psd:
                egginfo = os.path.join(path, 'EGG-INFO')
                if not os.path.isdir(egginfo):
                    continue

                name, requires = self._read_egginfo(egginfo)
                self._third_party_requires[name] = requires

        # get it
        if pkgname in self._third_party_requires:
            return pkgname, self._third_party_requires[pkgname]
        else:
            return (None, None)

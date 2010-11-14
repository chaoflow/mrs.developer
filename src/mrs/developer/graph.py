from mrs.developer.base import logger
from mrs.developer.base import Cmd
import sys
import os

try:
    import pygraphviz as pgv
except ImportError:
    print 'ERROR: could not import pygraphviz.'
    print ''
    print 'INSTALLATION:'
    print '- install graphviz: http://www.graphviz.org/'
    print '- install pygraphviz: http://networkx.lanl.gov/pygraphviz/'
    sys.exit(0)


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
    """Create a dependency graph using `graphviz`.
    """

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


    def __call__(self, dists=None, pargs=None):
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

        output_files = []

        # create a dotfile?
        if pargs.dotfile:
            graph.write(pargs.dotfile)
            output_files.append(pargs.dotfile)

        # now - create the output
        graph.layout()
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
            dir = os.path.join(src_dir, name)

            # is it a dir?
            if not os.path.isdir(dir):
                continue

            # does it have a .egg-info?
            egginfos = filter(lambda n: os.path.isdir(os.path.join(dir, n)) \
                                  and n.endswith('.egg-info'), os.listdir(dir))

            if len(egginfos) > 0:
                pkgname, requires = self._read_egginfo(os.path.join(
                        dir, egginfos[0]))
                dependencies[pkgname] = requires

        return self._reduce_extras(dependencies)

    def _reduce_extras(self, dependencies, remove_foreign_packages=True):
        """Reduces extras dependending in the requires of the other dists.
        """
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
                        subpkg, extra = dep.split(']', 1)[0].split('[', 1)
                        subpkg = subpkg.strip()
                        extra = extra.strip()

                        if subpkg in dependencies.keys():
                            changed = True
                            data[subpkg] = list(set(data[subpkg] +
                                                   dependencies[subpkg][extra]))
                            new_deps.append(subpkg)
                        elif not remove_foreign_packages:
                            if subpkg not in data:
                                data[subpkg] = []
                            new_deps.append(subpkg)

                    elif not remove_foreign_packages or dep in data.keys():
                        if dep not in data:
                            data[dep] = []
                        new_deps.append(dep)

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

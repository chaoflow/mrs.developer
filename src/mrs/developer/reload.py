from mrs.developer.base import Cmd
import base64
import re
import urllib
import urllib2


class default_value_string(str): pass


class Reload(Cmd):
    """Reload code while zope instance is running using `plone.reload`.
    """

    def __call__(self, dists=None, pargs=None):
        if pargs.list_instances:
            names = []
            for inst in self.cfg.get('reload', {}).get('instances', []):
                name = inst.get('name')
                if name:
                    names.append(name)
            return names

        if pargs.instance:
            # a instance is set, so let's override all default arguments
            # with the instance configuration, but keep the non default
            # argument values!

            instance_config = None
            for inst in self.cfg.get('reload', {}).get('instances', []):
                if inst.get('name') == pargs.instance:
                    instance_config = inst
                    break

            if instance_config:
                for key, ivalue in instance_config.items():
                    if isinstance(getattr(pargs, key, None),
                                  default_value_string):
                        setattr(pargs, key, ivalue)

        http_headers = {}
        http_data = {}

        # the action is either "code" or "zcml", but the zcml also reloads
        # the code...
        http_data['action'] = pargs.zcml and 'zcml' or 'code'

        # generate the ac_value cookie for authentication
        ac_value = ':'.join((pargs.username.encode('hex'),
                             pargs.password.encode('hex')))
        ac_value = str(base64.encodestring(ac_value)).strip()
        http_headers['Cookie'] = '__ac=%s' % ac_value

        # prepare the url
        url = 'http://%s:%s/@@reload' % (pargs.host, pargs.port)

        # make the request
        request = urllib2.Request(url, urllib.urlencode(http_data),
                                  http_headers)
        try:
            response = urllib2.urlopen(request)
        except urllib2.URLError, e:
            if getattr(e, 'code', '') == 404:
                return {'status': str(e),
                    'success': False,
                        'help': 'It seems that plone.reload is not installed '
                        'on your zope installation. Add plone.reload to your '
                        'eggs in the instance-section of your buildout.cfg '
                        'and re-run bin/buildout.'}
            else:
                return {'status': str(e),
                    'success': False}

        html = response.read()

        # parse response
        xpr = re.compile('<pre.*?>(.*?)</pre>', re.DOTALL)
        match = xpr.search(html)

        if match:
            # success
            result = {}
            resp_lines = match.groups()[0].split('\n')
            result['status'] = '\n'.join(resp_lines[:1]).strip()
            result['success'] = True
            if len(resp_lines)>1:
                result['files'] = resp_lines[2:]
            return result

        else:
            # failed
            return {'status': html,
                    'success': False}

    def _initialize(self):
        """Initializes the mrsd configuration
        """

        if not self.cfg.get('reload'):
            self.cfg.setdefault('reload', {'instances': []})

    def _defaults(self):
        """Returns a dict of some default values for arguments.
        The default values are guessed from the buildout configuration, if
        mrs.developer is defined as extension and buildout was executed.
        """

        defaults = {'username': 'admin',
                    'password': 'admin',
                    'port': 8080,
                    'host': 'localhost'}

        if self.cfg.get('reload', {}).get('instances'):
            instances = self.cfg['reload']['instances']
            if len(instances) > 1:
                defaults = instances[0].copy()

        return defaults

    def init_argparser(self, parser):
        """Add our arguments to a parser
        """

        defaults = self._defaults()

        parser.add_argument(
            '--zcml',
            dest='zcml',
            action='store_true',
            default=False,
            help='Reload ZCML too.')

        parser.add_argument(
            '--user',
            dest='username',
            action='store',
            default=default_value_string(defaults['username']),
            help='Zope-Username for logging into ZMI.')

        parser.add_argument(
            '--pass',
            dest='password',
            action='store',
            default=default_value_string(defaults['password']),
            help='Password of Zope-User (--user).')

        parser.add_argument(
            '--host',
            dest='host',
            action='store',
            default=default_value_string(defaults['host']),
            help='Hostname where zope is running at.')

        parser.add_argument(
            '--port',
            dest='port',
            action='store',
            default=default_value_string(defaults['port']),
            help='Port where zope is running at.')

        # register known instances
        if self.cfg.get('reload', {}).get('instances'):
            names = [part['name'] for part
                     in self.cfg.get('reload', {}).get('instances')]
            parser.add_argument(
                '--instance',
                choices=names,
                help='Select a zope instance to reload.')

        parser.add_argument(
            '--list-instances',
            dest='list_instances',
            action='store_true',
            default=False,
            help='Lists all available instances.')

    def _configure(self, buildout):
        """Called by the unload extension if mrsd.developer is defined in
        the extension of the buildout.
        This method looks up instance parts in buildout and stores host,
        port, username and password in the mrsd config file, which is then
        used as default values.
        """

        supported_recipes = ('collective.recipe.zope2cluster',
                             'plone.recipe.zope2instance')

        enabled_parts = buildout['buildout'].get('parts')

        for partname in enabled_parts.split():
            part = buildout.get(partname)
            inst = {}
            if part and part.get('recipe') in supported_recipes:
                # we have a zope instance

                # ... port
                try:
                    inst['port'] = int(part.get('http-address', 8080))
                except ValueError:
                    continue
                else:
                    if part.get('port-base'):
                        try:
                            inst['port'] += int(part.get('port-base'))
                        except ValueError:
                            continue

                # ip / host
                inst['host'] = part.get('ip-address', '0.0.0.0')

                # user
                user = part.get('user', 'admin:admin')
                inst['username'] = user.split(':', 1)[0]
                inst['password'] = user.split(':', 1)[1]

                # name
                inst['name'] = partname

                if inst:
                    self.cfg['reload']['instances'].append(inst)

        self.cmds.save_config()

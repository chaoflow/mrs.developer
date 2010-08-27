from mrs.developer.mrsd import CmdSet


class Extension(object):
    """Super-class for LoadExtension and UnloadExtension

    Load the mrsd command set, stores reference to buildout.
    """
    def __init__(self, buildout=None):
        self.buildout = buildout
        self.cmdset = CmdSet()


class LoadExtension(Extension):
    """Will inject mrsd develop eggs, if buildout is run

    By this we enable changes to setup.py being picked up:
      - entry-points
      - requires

    This is currently not possible with simple customized eggs, as buildout
    does not know about them.
    """
    def __call__(self):
        develop = self.buildout['buildout']['develop']
        ours = self.cmdset.cfg['develop']
        self.buildout['buildout']['develop'] = str("\n".join([develop] + ours))


class UnloadExtension(Extension):
    """Called after config is parsed
    """
    def __call__(self):
        self.cmdset.cmds['hookin']()


def load(buildout=None):
    return LoadExtension(buildout)()


def unload(buildout=None):
    return UnloadExtension()()


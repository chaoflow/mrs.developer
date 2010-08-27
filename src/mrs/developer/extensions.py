from mrs.developer.console_script import CmdSet


class LoadExtension(object):
    """Will inject mrsd develop eggs, if buildout is run

    By this everything will be properly done, e.g:
        install_requires, entry_point, version pinning conflicts


    Eggs in eggs-customized cannot take influence on these. Just code changes
    in there.
    """
    def __init__(self, buildout):
        self.buildout = buildout

    def __call__(self):
        develop = self.buildout['buildout']['develop']
        ours = "src-mrsd/zodict"
        self.buildout['buildout']['develop'] = "\n".join([develop, ours])


class UnloadExtension(object):
    """Called after config is parsed
    """
    def __call__(self):
        cmdset = CmdSet()
        cmdset.cmds['hookin']()


def load(buildout=None):
    return LoadExtension(buildout)()


def unload(buildout=None):
    return UnloadExtension()()


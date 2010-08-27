from mrs.developer.console_script import CmdSet


class UnloadExtension(object):
    """Called after config is parsed
    """
    def __call__(self):
        cmdset = CmdSet()
        cmdset.cmds['hookin']()


def unload(buildout=None):
    return UnloadExtension()()


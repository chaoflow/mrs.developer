from subprocess import check_call as real_check_call

import logging
logger = logging.getLogger("mrsd")


def check_call(*args, **kws):
    """wrap subprocess.check_call for logging
    """
    logger.info(args, kws)
    real_check_call(*args, **kws)


class Cmd(object):
    """An abstract command

    subclasses need to implement __call__ and may implement _initialize
    """
    @property
    def cfg(self):
        return self.parent.cfg

    @property
    def root(self):
        return self.parent.root

    def __init__(self, name, parent):
        self.__name__ = name
        self.parent = parent
        try:
            self._initialize()
        except AttributeError:
            pass

    def init_argparser(self, parser):
        pass

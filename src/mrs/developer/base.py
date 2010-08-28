
import logging
logging.basicConfig()
logger = logging.getLogger("mrsd")

class Cmd(object):
    """An abstract command

    subclasses need to implement __call__ and may implement _initialize
    """
    @property
    def cfg(self):
        return self.parent.cfg

    def __init__(self, name, parent):
        self.__name__ = name
        self.parent = parent
        try:
            self._initialize()
        except AttributeError:
            pass

    def init_argparser(self, parser):
        pass



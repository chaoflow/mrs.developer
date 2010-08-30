from mrs.developer.base import Cmd


class Build(Cmd):
    """building with buildout (and others)
    """
    def __call__(self, egg_name):
        check_call(['git', 'init'],
                cwd=custom_path, stdout=PIPE, stderr=PIPE)
        check_call(['git', 'add', '.'],
                cwd=custom_path, stdout=PIPE, stderr=PIPE)
        check_call(['git', 'commit', '-m', 'initial from: %s' % (stock_path,)],
                cwd=custom_path, stdout=PIPE, stderr=PIPE)
        check_call(['git', 'tag', 'initial'],
                cwd=custom_path, stdout=PIPE, stderr=PIPE)


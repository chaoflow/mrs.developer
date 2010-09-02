import os
import tempfile
import subprocess
import plone.testing


class MrsDeveloperFixture(plone.testing.Layer):

    def setUp(self):
        dst = tempfile.mkdtemp()
        src = os.path.join(os.path.dirname(__file__), 'tests', 'test_skel')
        buildout_dir = os.path.join(src, '..', '..', '..', '..', '..')
        subprocess.check_call('cp -R '+src+'/* '+dst, shell=True)
        subprocess.check_call("sed 's/<mrsd-develop-path>/" + \
                              buildout_dir.replace('/', '\/') + \
                              "/' init.cfg.in > init.cfg",
                              cwd=dst, shell=True)
        subprocess.check_call("sed 's/<mrsd-develop-path>/" + \
                              buildout_dir.replace('/', '\/') + \
                              "/' buildout.cfg.in > buildout.cfg",
                              cwd=dst, shell=True)
        subprocess.check_call(os.path.abspath(buildout_dir+'/bin/python') + \
                              ' bootstrap.py', cwd=dst, shell=True)
        subprocess.check_call('./bin/buildout -vc init.cfg', cwd=dst, shell=True)
        subprocess.check_call('./bin/buildout -v', cwd=dst, shell=True)
        self['buildout-directory'] = dst

    def tearDown(self):
        subprocess.check_call('rm '+self['buildout-directory']+'* -R', shell=True)

    def testSetUp(self):
        pass

    def testTearDown(self):
        pass

MRS_DEVELOPER_FIXTURE = MrsDeveloperFixture()

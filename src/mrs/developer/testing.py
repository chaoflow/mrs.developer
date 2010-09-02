import os
import tempfile
import subprocess
import plone.testing


class MrsDeveloperFixture(plone.testing.Layer):

    def setUp(self):
        dst = tempfile.mkdtemp()
        src = os.path.join(os.path.dirname(__file__), 'tests', 'test_skel')
        subprocess.check_call('cp -R ' + src + '/* ' + dst, shell=True)
        subprocess.check_call("ln -s " + os.path.abspath(os.path.join(
                                src, '..', '..', '..', '..', '..')),
                    cwd=dst, shell=True)
        subprocess.check_call('./mrs.developer/bin/python bootstrap.py',
                    cwd=dst, shell=True)
        subprocess.check_call('./bin/buildout -vc init.cfg',
                    cwd=dst, shell=True)
        subprocess.check_call('./bin/buildout -v',
                    cwd=dst, shell=True)
        self['buildout-directory'] = dst

    def tearDown(self):
        subprocess.check_call('rm ' + self['buildout-directory'] + '* -R',
                    shell=True)

    def testSetUp(self):
        pass

    def testTearDown(self):
        pass

MRS_DEVELOPER_FIXTURE = MrsDeveloperFixture()

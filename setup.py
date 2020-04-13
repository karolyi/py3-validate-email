from pathlib import Path
from shutil import move, rmtree
from subprocess import check_call
from tempfile import mkdtemp

from setuptools import find_packages, setup
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop
from setuptools.command.sdist import sdist

try:
    # OSX Homebrew fix: https://stackoverflow.com/a/53190037/1067833
    from sys import _base_executable as executable
except ImportError:
    from sys import executable

_EGG_REQ_PATH = Path(__file__).parent.joinpath(
    'py3_validate_email.egg-info', 'requires.txt')
_REQ_PATH = Path(__file__).parent.joinpath('requirements.txt')

with open(_REQ_PATH if _REQ_PATH.exists() else _EGG_REQ_PATH) as fd:
    _req_content = fd.readlines()
_DEPENDENCIES = [x.strip() for x in _req_content if x.strip()]

with open(Path(__file__).parent.joinpath('README.rst')) as fd:
    _LONG_DESC = fd.read()


def run_initial_updater():
    'Download an initial blacklist.txt on install time.'
    # Install dependencies so the initial update can run
    check_call([executable, '-m', 'pip', 'install'] + _DEPENDENCIES)
    # The updater will walk code stack frames and see if this
    # variable is set in locals() to determine if it is run from the
    # setup, in which case it won't autoupdate.
    _IS_VALIDATEEMAIL_SETUP = True
    from validate_email.updater import BlacklistUpdater, LIB_PATH_DEFAULT
    LIB_PATH_DEFAULT.mkdir(exist_ok=True)
    blacklist_updater = BlacklistUpdater()
    blacklist_updater._is_install_time = _IS_VALIDATEEMAIL_SETUP
    blacklist_updater.process(force=True)


class DevelopCommand(develop):
    'Develop command.'

    def run(self):
        if self.dry_run:
            return super().run()
        run_initial_updater()
        super().run()


class SdistCommand(sdist):
    'Sdist command.'

    def run(self):
        """
        Manually remove the data directory before creating the
        distribution package, every install will create it for
        themselves when installing created the python wheel.
        `MANIFEST.in` should not remove the data dir since install and
        develop/install would exclude it!
        """
        if self.dry_run:
            return super().run()
        tempdir = Path(mkdtemp()).joinpath('data')
        data_dir = Path(
            __file__).absolute().parent.joinpath('validate_email', 'data')
        do_move = data_dir.exists()
        if do_move:
            move(src=data_dir, dst=tempdir)
        super().run()
        if do_move:
            move(src=tempdir, dst=data_dir)
            rmtree(path=tempdir.parent)


class BuildPyCommand(build_py):
    'BuildPy command.'

    def run(self):
        if self.dry_run:
            return super().run()
        run_initial_updater()
        super().run()


setup(
    name='py3-validate-email',
    version='0.2.6',
    packages=find_packages(exclude=['tests']),
    install_requires=_DEPENDENCIES,
    author='László Károlyi',
    author_email='laszlo@karolyi.hu',
    include_package_data=True,
    description=(
        'Email validator with regex, blacklisted domains and SMTP checking.'),
    long_description=_LONG_DESC,
    long_description_content_type='text/x-rst',
    keywords='email validation verification mx verify',
    url='http://github.com/karolyi/py3-validate-email',
    cmdclass=dict(
        develop=DevelopCommand, sdist=SdistCommand, build_py=BuildPyCommand),
    license='LGPL',
)

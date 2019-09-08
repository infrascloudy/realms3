import os
from pipenv.project import Project
from pipenv.utils import convert_deps_to_pip
from setuptools import setup, find_packages

pipfile = Project().parsed_pipfile
requirements = convert_deps_to_pip(pipfile['packages'], r=False)

if os.environ.get('USER', '') == 'vagrant':
    del os.link

DESCRIPTION = "Simple git based wiki"

with open('README.md') as f:
    LONG_DESCRIPTION = f.read()

__version__ = None
exec(open('realms3/version.py').read())

CLASSIFIERS = [
    'Intended Audience :: Developers',
    'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
    'Operating System :: POSIX :: Linux',
    'Programming Language :: Python',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content']

setup(
    name='realms3',
    version=__version__,
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'realms-wiki = realms.commands:cli'
        ]},
    author='Infrascloudy',
    author_email='support@infrascloudy.io',
    maintainer='Infrascloudy',
    maintainer_email='support@infrascloudy.io',
    url='https://github.com/infrascloudy/realms3',
    license='GPLv2',
    include_package_data=True,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    platforms=['any'],
    classifiers=CLASSIFIERS
)

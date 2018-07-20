from pathlib import Path
from setuptools import setup, find_packages

version = '1.0.0'

name = 'solar_loader'
description = 'load radiation data in the scope of solar project for IBGE'
url = 'https://gitlab.com/atelier-cartographique/be-lb/solar-loader'
author = 'Atelier Cartographique'
author_email = 'contact@atelier-cartographique.be'
license = 'Affero GPL3'

classifiers = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
    'Operating System :: POSIX',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3.5',
]

install_requires = [
    'django', 'numpy', 'psycopg2', 'shapely', 'click', 'attrs', 'munch',
    'pysolar', 'pyproj'
]

packages = find_packages()

setup(
    name=name,
    version=version,
    url=url,
    license=license,
    description=description,
    author=author,
    author_email=author_email,
    packages=packages,
    include_package_data=True,
    install_requires=install_requires,
    classifiers=classifiers,
)

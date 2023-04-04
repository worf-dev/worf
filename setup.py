from distutils.core import setup
from setuptools import find_packages
from req import reqs

setup(
    name='worf',
    python_requires='>=3',
    version='0.0.1',
    author='Andreas Dewes - 7scientists',
    author_email='andreas.dewes@7scientists.com',
    license='proprietary',
    url='https://gitlab.com/7scientists/worf',
    packages=find_packages(),
#    package_data={'': ['*.ini']},
    include_package_data=True,
    install_requires=reqs,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'worf = worf.cli.main:main'
        ]
    },
    description='Our authentication API.',
    long_description="""Our authentication API.
"""
)

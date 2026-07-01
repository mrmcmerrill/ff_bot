from setuptools import setup, find_packages

setup(
    name='ff_bot',

    packages=find_packages(exclude=['ff_bot.tests', 'ff_bot.tests.*']),

    include_package_data=True,

    # Ship the frozen season snapshots so all-time reports work from an installed package.
    package_data={'ff_bot': ['data/*/*.json']},

    version='2.0.0',

    description='Fantasy Football Chat Bot (ESPN & Sleeper)',

    author='Robert McClary',

    author_email='rmcclary.30@gmail.com',

    install_requires=[
        'requests>=2.31.0,<3.0.0',
        'espn_api>=0.46.0,<1.0.0',
        'apscheduler>=3.10.0,<4.0.0',
    ],

    extras_require={
        'test': ['pytest>=8.0.0', 'requests_mock>=1.12.0'],
    },

    python_requires='>=3.9',

    url='https://github.com/mrmcmerrill/ff_bot',

    classifiers=[
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)

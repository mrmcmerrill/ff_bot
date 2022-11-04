from setuptools import setup

setup(
    name='ff_bot',

    packages=['ff_bot'],

    include_package_data=True,

    version='1.1.0',

    description='Fantasy Football Chat Bot',

    author='Robert McClary',

    author_email='rmcclary.30@gmail.com',

    install_requires=['requests>=2.0.0,<3.0.0', 'espn_api>=0.26.0', 'apscheduler>3.0.0,<4.0.0', 'datetime'],

    test_suite='nose.collector',

    tests_require=['nose', 'requests_mock'],

    url='https://github.com/mrmcmerrill/ff_bot',

    classifiers=[
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)

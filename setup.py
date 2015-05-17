from setuptools import setup

setup(
    name='parophrys',
    version='0.1.0',
    py_modules=['parophrys'],
    include_package_data=True,
    install_requires=[
        'click',
        'paramiko',
    ],
    entry_points='''
        [console_scripts]
        paro=paro:cli
    ''',
)

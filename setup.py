from setuptools import setup, find_packages

setup(
    name='parophrys',
    version='0.2.0',
    py_modules=['parophrys'],
    packages=find_packages(),
    include_package_data=True,
    author='Ryan Whitehurst',
    author_email='ryan@ryanwhitehurst.com',
    url='https://github.com/thrnio/parophrys',
    license='Apache License 2.0',
    install_requires=[
        'click',
        'paramiko',
    ],
    entry_points='''
        [console_scripts]
        paro=parophrys.paro:cli
    ''',
)

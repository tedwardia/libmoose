from setuptools import setup

setup(
    name='libmoose',
    version='0.1',
    packages=['libmoose'],
    install_requires=[
        'requests',
		'elasticsearch>=7.17.0, <8',
    ],
)

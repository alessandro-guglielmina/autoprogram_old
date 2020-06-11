try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

config = {
'description': 'Automate programs',
'author': 'Alessandro Guglielmina',
'url': '/',
'download_url': '/',
'author_email': 'alessandro.guglielmina@gmail.com',
'version': '0.1',
'install_requires': ['nose'],
'packages': ['AutoProgram'],
'scripts': [],
'name': 'projectname'
}

setup(**config)
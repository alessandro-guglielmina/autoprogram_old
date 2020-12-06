try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

config = {
'description': 'Automate VGPro part programming',
'author': 'Alessandro Guglielmina',
'url': '/',
'download_url': '/',
'author_email': 'alessandro.guglielmina@gmail.com',
'version': '1.0',
'install_requires': [],
'packages': [],
'scripts': [],
'name': 'autoprogram'
}

setup(**config)
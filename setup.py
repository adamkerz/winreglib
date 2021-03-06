from setuptools import setup


from winreglib import __version__
with open('README.rst') as fin: long_decription=fin.read()

setup(
    name='winreglib',
    version=__version__,

    py_modules=['winreglib'],

    # PyPI MetaData
    author='Adam Kerz',
    author_email='github@kerz.id.au',
    description='High level, class based Windows registry manipulation',
    long_description=long_decription,
    license='BSD 3-Clause',
    keywords='winreg',
    url='https://github.com/adamkerz/winreglib',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],

    zip_safe=False,
)

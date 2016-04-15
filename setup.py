from setuptools import setup,find_packages,Command


with open('version.py') as fin: exec(fin.read())


setup(
    name='winreglib',
    version=__version__,

    py_modules=['winreglib'],

    # PyPI MetaData
    author='Adam Kerz',
    author_email='github@kerz.id.au',
    description='High level Windows registry manipulation',
    license='BSD 3-Clause',
    keywords='winreg',
    url='',
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ),

    zip_safe=False,
)

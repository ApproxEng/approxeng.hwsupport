from setuptools import setup, find_namespace_packages

setup(
    name='approxeng.hwsupport',
    version='0.1.0',
    author='Tom Oinn',
    author_email='tomoinn@gmail.com',
    url='https://github.com/ApproxEng/approxeng.hwsupport',
    description='Python robot hardware driver support',
    classifiers=['Programming Language :: Python :: 3.6'],
    packages=find_namespace_packages(),
    install_requires=['future-fstrings', 'pyyaml'],
)

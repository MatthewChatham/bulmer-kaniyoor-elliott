from setuptools import setup, find_packages

with open('../requirements.txt', 'r') as f:
    requirements = [
        str.strip(fn) 
        for fn in f.read().split('\n') 
        if not fn.startswith('-e')
        and not fn.startswith('.')
    ]

setup(
    name='src',
    version='1.0.1',
    author='Matthew Chatham',
    author_email='matthew.a.chatham@gmail.com',
    description='CNT Meta-Analysis Explorer',
    packages=find_packages(),
    install_requires=requirements,
)
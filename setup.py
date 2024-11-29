from setuptools import setup, find_packages

setup(
    name='wormhole-core',
    version='0.1.0',                    
    packages=find_packages(),
    author='p1tsi',                 
    author_email='pitsistip@gmail.com',  
    description='Wormhole core',
    long_description=open('README.md').read(),  
    long_description_content_type='text/markdown',
    url='https://github.com/p1tsi/wormhole-core',
    python_requires='>=3.8',             
)

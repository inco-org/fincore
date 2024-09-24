from setuptools import setup, find_packages

setup(
    name='fincore',
    version='3.0.3',
    description='A financial core library',
    author='Rafael Viotti',
    author_email='viotti@inco.vc',
    url='https://github.com/inco-org/fincore',
    packages=find_packages(),
    py_modules=['fincore'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    install_requires=['typeguard', 'python-dateutil'],
    python_requires='>=3.9'
)

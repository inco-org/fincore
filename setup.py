import os
import shutil
from setuptools import setup, find_packages
from setuptools.command.install_scripts import install_scripts as InstallScripts

class CustomInstallScripts(InstallScripts):
    def run(self):
        src_main = os.path.join(os.path.dirname(__file__), '__main__.py')

        if not os.path.exists(self.build_dir):
            os.makedirs(self.build_dir)

        target_script = os.path.join(self.build_dir, 'fincore')

        shutil.copy(src_main, target_script)

        os.chmod(target_script, 0o755)

        self.scripts = [target_script]

        InstallScripts.run(self)

setup(
    name='fincore',
    version='4.6.0',
    description='A financial core library',
    author='Rafael Viotti',
    author_email='viotti@inco.vc',
    url='https://github.com/inco-org/fincore',
    packages=find_packages(),
    py_modules=['fincore'],
    scripts=['__main__.py'],  # Required to trigger the install_scripts hook
    cmdclass={'install_scripts': CustomInstallScripts},
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    install_requires=['typeguard', 'python-dateutil'],
    python_requires='>=3.9'
)

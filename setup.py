import sys
# Remove current dir from sys.path, otherwise setuptools will peek up our
# module instead of system's.
sys.path.pop(0)
from setuptools import setup
sys.path.append(".")
import sdist_upip

setup(name='micropython-iotc',
      version='1.0.3',
      description='Azure IoT Central client for MicroPython (mqtt protocol)',
      long_description='',
      url='https://github.com/iot-for-all/iotc-micropython-client',
      author='Luca Druda',
      author_email='ludruda@microsoft.com',
      maintainer='IoT Central Developers',
      license='MIT',
      cmdclass={'sdist': sdist_upip.sdist},
      packages=['iotc'])
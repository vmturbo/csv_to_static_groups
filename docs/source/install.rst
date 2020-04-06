.. _CPython: https://www.python.org
.. _Requests: http://docs.python-requests.org/en/master/
.. _vmt-connect: https://github.com/turbonomic/vmt-connect

Intallation
***********
*csv_to_static_groups* can be placed in any directory, although scripts are
typically stored in */srv/tomcat/script/control/* on a Turbonomic instance.

PyPi installation is not currently supported via pip or setuptools

Requirements
============
*csv_to_static_groups* requires a supported version of Python, the requests_ module,
and vmt-connect_ in the same directory.

- CPython_ >= 3.3
- requests_ >= 2.10.0
- vmt-connect_ >= 2.0.0

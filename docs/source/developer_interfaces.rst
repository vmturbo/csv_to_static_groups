Developer Interfaces
********************

*csv_to_static_groups* has 3 objects that can be used to manage static groups or
parse csvs into groups within your own scripts.

Additionally, the main function of the script can be used to leverage all of the
logic within another script.

Please browse the `example scripts <https://github.com/vmturbo/csv_to_static_groups/tree/master/examples>`_.

.. module:: csv_to_static_groups

StaticGroup
===========
.. autoclass:: StaticGroup
   :show-inheritance:
   :inherited-members:

Exceptions
----------
.. autoexception:: StaticGroupError
.. autoexception:: GroupAlreadyExistsError
.. autoexception:: MissingUUIDError
.. autoexception:: NoMatchingGroupError
.. autoexception:: DuplicateMatchingGroupError
.. autoexception:: LookupNameError
.. autoexception:: NameMatchError
.. autoexception:: MultipleMatchingNamesError

CSVGroupParser
==============
.. autoclass:: CSVGroupParser
   :show-inheritance:
   :inherited-members:

Exceptions
----------
.. autoexception:: CSVGroupParserError
.. autoexception:: MissingHeaderError

GroupUpdateUtility
==================
.. autoclass:: GroupUpdateUtility
   :show-inheritance:
   :inherited-members:

main
====
.. autofunction:: main

Global Variables
----------------

Logging/Output
++++++++++++++

LOGGER (logging.logger)
  - Set to your logging.logger to include log entries
  - Default: ``None``

QUIET (bool)
  - Allows ouput to sysout
  - Default: ``True``

TRACE (bool)
  - Outputs trace to LOGGER
  - Default: ``True``

WARN (bool):
  - Allow warnings in sysout
  - Default: ``True``

Summary Names
+++++++++++++
Change categories available to main's return dictionary.

- TRK_DELETE = ``"Deleted"``
- TRK_ERROR = ``"Errors"``
- TRK_MISS_ENTITY = ``"Missing Entities"``
- TRK_ADD = ``"Added"``
- TRK_UPDATE = ``"Updated"``
- TRK_SKIP = ``"Skipped"``

GroupParser Fields
++++++++++++++++++
Default CSV Headers

- ENTITY_TYPE_HEADER = ``"Entity Type"``
- ENTITY_NAME_HEADER = ``"Entity Name"``
- GROUP_DELIMITER = ``"_"``

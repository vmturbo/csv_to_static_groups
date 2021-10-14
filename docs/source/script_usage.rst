Script Usage
************

Simple Usage
============

.. code:: bash

    $ ./csv_to_static_groups.py sample_csv.csv -u administrator


Script Options
--------------
Required Arguments (In positional order)

+--------------------------+----------------------------------+
| ``"input_csv"``          | Path to input csv                |
+--------------------------+----------------------------------+

Optional arguments. Text between quotations indicates user specified content.

+-------------------------------------------+--------------------------------------+
| ``-h``, ``--help``                        | Show options.                        |
+-------------------------------------------+--------------------------------------+
| ``-u "USERNAME"``,                        | Turbonomic Username, Password will be|
| ``--username "USERNAME"``                 | prompted.                            |
+-------------------------------------------+--------------------------------------+
|``--encoded_creds "ENCODED_CREDS"``:sup:`†`| Base64 encoded credentials. Use this |
|                                           | to provide all credentials without   |
|                                           | entering a password each time.       |
+-------------------------------------------+--------------------------------------+
| ``-t "TARGET"`` , ``--target "TARGET"``   | Turbonomic server address.           |
|                                           | Default=localhost                    |
+-------------------------------------------+--------------------------------------+
| ``--no_add``                              | Prevents adding entities when        |
|                                           | updating groups                      |
+-------------------------------------------+--------------------------------------+
| ``--no_remove``                           | Prevents removing entities when      |
|                                           | updating groups                      |
+-------------------------------------------+--------------------------------------+
| ``--delete``                              | Delete groups that match csv         |
+-------------------------------------------+--------------------------------------+
| ``--case_insensitive``                    | Match entity names without           |
|                                           | case-sensitivity                     |
+-------------------------------------------+--------------------------------------+
| ``--group_delimiter "GROUP_DELIMITER"``   | String to separate grouping values.  |
|                                           | Default='_'                          |
+-------------------------------------------+--------------------------------------+
| ``--group_headers  "GROUP_HEADERS" ...``  | CSV Headers to group on. By default  |
|                                           | all columns except 'Entity Type' and |
|                                           | 'Entity Name' are used in order from |
|                                           | left to right                        |
+-------------------------------------------+--------------------------------------+
| ``--dryrun``                              | Prevents commits to the Turbonomic   |
|                                           | server                               |
+-------------------------------------------+--------------------------------------+
| ``--no_warn``                             | Disable warning output to console    |
+-------------------------------------------+--------------------------------------+
| ``-q``, ``--quiet``                       | Suppress output to console           |
+-------------------------------------------+--------------------------------------+
| ``--log "LOG"``                           | Path to file record log entries      |
+-------------------------------------------+--------------------------------------+
| ``--ignore_insecure_warning``             | Suppress insecure HTTPS request      |
|                                           | warnings                             |
+-------------------------------------------+--------------------------------------+
| ``--config "CONFIG"``                     | Path to JSON Config file with        |
|                                           | arguments                            |
+-------------------------------------------+--------------------------------------+
| ``--active_only``                         | If duplicate names for an entity are |
|                                           | found only add the active one unless |
|                                           | multiple active entities are found   |
|                                           |                                      |
|                                           | **NOTE:** Intended for Distaster     |
|                                           | Recovery senarios where an *active*  |
|                                           | and *passive* virtual machine with   |
|                                           | the same name exists                 |
+-------------------------------------------+--------------------------------------+

:sup:`† encoded_creds can be generated with this command
(Remember to disable console history so the credentials are not stored)`::

    $ echo -n "username:password" | base64

Using a Config File
-------------------
All options can be specified in a single json formatted file for quick option
configurations.

Options passed with a config file will override any overlapping CLI arguments.

An example config file could be:

*sample_config.json*::

    {
      "encoded_creds":"dXNlcm5hbWU6cGFzc3dvcmQ=",
      "target": "some_ip",
      "case_insensitive": true,
      "quiet": true,
      "log": "/somepath/logfile.log"
    }

Then run it with:

.. code:: bash

    $ ./csv_to_static_groups.py sample_csv.csv --config sample_config.json

Importing As A Module
=====================

*csv_to_static_groups* can be imported to create your own CSV to static group
script, create/update/delete static groups without a csv, or incorporate the
main *csv_to_static_groups* function anywhere within your script.

.. code:: python

    import vmtconnect
    import csv_to_static_groups

    conn = vmtconnect.VMTConnection(host='localhost', username='austin',
                                    password='*****')

    my_group = csv_to_static_groups.StaticGroup(conn, "My Group", "VirtualMachine",
                                               ["SampleVM1", "SampleVM2"])
    my_group.add_or_update(lookup_names=True)


Please reference the :doc:`developer interfaces documentation </developer_interfaces>` and `code examples <https://github.com/vmturbo/csv_to_static_groups/tree/master/examples>`_.

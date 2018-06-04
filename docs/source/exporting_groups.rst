Exporting Groups to CSV
***********************

Some users may find the need to export custom groups.

Individual groups can be exported to CSV using Turbonomic's UI:

    .. image:: ../media/group_to_csv.gif
        :scale: 40%

For exporting all groups in a Turbonomic instance, you can use the
`export_groups_to_csv.py example script <https://github.com/vmturbo/csv_to_static_groups/blob/master/examples/export_groups_to_csv.py>`_.

Installation
============

Place *export_groups_to_csv.py* into the same directory as *csv_to_static_groups.py* and *vmtconnect.py*

Script Usage
============

.. code:: bash

    $ ./export_groups_to_csv.py output.csv -u administrator

Sample Output
-------------

    .. image:: ../media/export_csv.png
        :scale: 40%

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
| ``--all_groups``                          | Also export non-custom Turbonomic    |
|                                           | groups                               |
+-------------------------------------------+--------------------------------------+
| ``--include_group_type``                  | Include a column to indicate if a    |
|                                           | group is static or dynamic           |
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
| ``--ignore_insecure_warning``             | Supress insecure HTTPS request       |
|                                           | warnings                             |
+-------------------------------------------+--------------------------------------+
| ``--config "CONFIG"``                     | Path to JSON Config file with        |
|                                           | arguments                            |
+-------------------------------------------+--------------------------------------+

:sup:`† encoded_creds can be generated with this command
(Remember to disable console history so the credentials are not stored)`::

    $ echo -n "username:password" | base64

Using a Config File
-------------------

See `csv_to_static_groups doc <script_usage.html#using-a-config-file>`__.

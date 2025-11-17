Server
=====
Introduction
--------------
The server is a virtual machine hosted by Uppsala University, running Ubuntu.

Current specifications (can be scaled as needed):

:vCPUs: 8
:RAM (GiB): 32
:Disk space (GiB): 250
:OS: Ubuntu 24.04 LTS

The server runs `Neurodesk <https://neurodesk.org/>`_ in a Docker container, which can be accessed via a web browser. Neurodesk provides a remote desktop with many built in tools for neuroimaging and neurophysiology preprocessing, analysis, and visualization.

.. youtube:: Hx2shbKDz9o
   :width: 640
   :height: 360

Getting access
---------------
Getting access to the server involves a few steps, but once your instance of Neurodesk is running, you can access it via a simple, bookmarkable, link.

Easy route
^^^^^^^^^^
Contact admin ``Jonas Persson`` for help.
Together you will make sure you can access the server with your Akka-credentials,
mount your Argos storage,
and launch Neurodesk.
Once you have access to Neurodesk in your browser, make sure to bookmark the link for future access.

Advanced route
^^^^^^^^^^^^^^^

Prerequisites
*************
To gain access to the server, you need to be a member of the right AD-group, which is administered through Akka.
You can test if you have access by opening a terminal/run cmd and run ``ssh akkaid@serverip`` and enter your Password A.
If you cannot gain access, you need to contact your admin or helpdesk to be added to the right group.

.. note:: AD-group and server-ip can be found in the file ``server_secrets.txt`` in Allvis.

If you can access the server, now is the time to ask your admin to setup the proper permissions to mount Argos/UPPMAX and run docker.
Once that is done, you start Neurodesk by running a shell script ``/srv/scripts/run_neurodesktop_version.sh version`` where ``version`` specifies what version of Neurodesk you want to run. You can find possible entries here: <https://hub.docker.com/r/vnmd/neurodesktop/tags>

.. warning:: If you do not specify a version, Neurodesk will lauch with the tag ``latest``. While this works, it is strongly recommended to always specify version, and document what version you are running, to be able to reproduce your results (and for easier troubleshooting).

.. note:: As of now, versions later than ``2025-06-10`` do not work properly on this server.

Usage
-------


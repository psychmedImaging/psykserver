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
Getting access to the server involves a few steps, but once your instance of Neurodesktop is running, you can access it via a simple, bookmarkable, link.

Easy route
^^^^^^^^^^
Contact admin ``Jonas Persson`` for help.
Together you will make sure you can access the server with your Akka-credentials,
mount your Argos storage,
and launch Neurodesktop.
Once you have access to Neurodesktop in your browser, make sure to bookmark the link for future access.

Advanced route
^^^^^^^^^^^^^^^

Prerequisites
*************
To gain access to the server, you need to be a member of the right AD-group, which is administered through Akka.
You can test if you have access by opening a terminal/run cmd and run ``ssh akkaid@serverip`` and enter your Password A.
If you cannot gain access, you need to contact your admin or helpdesk to be added to the right group.

.. note:: AD-group and server-ip can be found in the file ``server_secrets.txt`` in Allvis.

If you can access the server, now is the time to ask your admin to setup the proper permissions to mount Argos/UPPMAX and run docker.
Once that is done, you start Neurodesktop by running a shell script ``/srv/scripts/run_neurodesktop_version.sh version`` where ``version`` specifies what version of Neurodesktop you want to run. You can find possible entries here: https://hub.docker.com/r/vnmd/neurodesktop/tags.

.. warning:: If you do not specify a version, Neurodesktop will lauch with the tag ``latest``. While this works, it is strongly recommended to always specify version, and document what version you are running, to be able to reproduce your results (and for easier troubleshooting).

.. note:: As of now, versions later than ``2025-06-10`` do not work properly on this server.

Usage
-------
.. warning:: Since Neurodesk runs in a container, files that are created or modified in it will be removed if the server needs to restart. Therefore, you should rely on the filesystems that are mounted in it. The folder ``/data`` is your storage space on the server. Anything stored here will be stored in ``/storage/akka-id`` on the server. The subfolder ``/data/argos`` contains the group folders that you have access to on Argos. In general, it is recommended that you use the Argos storage. If you have an UPPMAX project and have its "wharf" mounted, this will be accessible under ``/data/wharf``.

There are two main ways to interact with Neurodesktop, via the JupyterLab interface or via a remote desktop.

JupyterLab
***********
This is your starting point when logging in to Neurodesktop. Here, you can work with notebooks, access a terminal, and manage files. There are many tutorials available on the `Neurodesk homepage <https://neurodesk.org/example-notebooks/intro.html>`_ with example Jupyter Notebooks to get you started.

Remote desktop
***************
By clicking Neurodesktop in the JupyterLab launcher, you can access a remote desktop. Select one of the two options (try and see which one works best for you, which may depend on OS and browser). Here you can lauch several GUI based applications. If you want to run e.g. Matlab, RStudio, or VS Code, you can do so here. There are also many standalone applications available. The remote desktop is more flexible for visualization and interactive plots than matplotlib in JupyterLab.

Accessing Neurodesktop
^^^^^^^^^^^^^^^^^^^^^^^
Option 1: Web browser
*********************
The quickest way to access Neurodesktop is via your browser. Simply open the link that appears in the terminal after running the startup script. You will reach JupyterLab from which you can access a remote desktop (click the Neurodesktop icon in the launcher). RDP and VNC both have their advantages and disadvantages. Pick the one that works best. A common limitation is that some key combinations (e.g. alt gr + key) might not work as well as copy/pasting from other applications.

Option 2: Neurodesk App
************************
It is also possible to install a standalone software for accessing Neurodesktop (see instructions here: `<https://neurodesk.org/getting-started/local/neurodeskapp/>`_). After launching the app, click "connect to remote server..." and in the top field, enter the link you got from the startup script. This solution tends to work better with copy/pasting but has the saem limitations regarding keyboard usage.

Option 3: Remote desktop client
*********************************
Finally, it is possible to access the remote desktop through a RDP client, such as Remmina in Linux or Remote Desktop Connection in Windows. This is usually the most compatible solution for copy/pasting and key combinations. For this to work, you first need to set the password for the user jovyan within Neurodesktop. Open a terminal after accessing Neurodesktop through e.g. your browser and type ``sudo passwd jovyan`` to set a password. After this, you can use your RDP client to connect.  

In Remmina (Linux):

:Protocol: RDP - Remote Desktop Protocol
:Server: ``server-ip:3390``
:Username: jovyan
:Password: the password that you set

Click Save and Connect

In Remote Desktop Connection (Windows):

:Computer: ``server-ip:3390``
:User name: jovyan

Click connect and enter password when prompted.

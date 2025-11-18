UPPMAX
========

TEST
------------
See :doc:`Custom link text <../../../uppmax/config/fmriprep-config-template.json>`_

.. note::
UPPMAX provides high-performance computing (HPC) and enables running containerized processing pipelines, such as the so called BIDSapps for neuroimaging data, in a highly parallelized fashion.

Below is an outline of a typical workflow for multimodal MRI data:

.. graphviz::

   digraph {
      subgraph cluster0 {
         node [style=filled,color=white];
         style=filled;
         color=lightgrey;
         "anat" [shape=box];
         "dwi" [shape=box];
         "fmri" [shape=box];
         label = "raw data";
      }
      subgraph cluster1 {
         "anat" -> "mriqc";
         "dwi" -> "mriqc";
         "fmri" -> "mriqc";
         "fmri" -> "fmriprep";
         "anat" -> "fmriprep";
         "anat" -> "qsiprep";
         "anat" -> "freesurfer";
         "dwi" -> "qsiprep";
         "qsiprep" -> "qsirecon";
         subgraph cluster2 {
            "xcp_d";
            label = "rs-fmri";
            labelloc=b;
         }
         "fmriprep" -> "xcp_d";
         "freesurfer" -> "fmriprep";
         "freesurfer" -> "qsirecon";
         subgraph cluster3 {
            "fitlins";
            label = "task-fmri";
            labelloc=b;
         }
         "fmriprep" -> "fitlins";
         label = "processing pipelines";
         labelloc=b;
      }
   }
Getting access
---------------
In order to use UPPMAX, you need access to a project. To gain access to a SNIC SENS Medium project, contact PI Jonas Persson.

Logging in and transferring files
------------------------------------
You log in to a SENS project with ssh:

.. code-block:: shell

   ssh [userid]@bianca.uppmax.uu.se

You will be prompted for a password and two-factor authentication. Unless you logged in recently, the login node is likely down and will take a few minutes to start up, after which you need to enter the password again. After logging in, you will be met with a linux shell and are now ready to run jobs.
The SENS projects are made to handle sensitive data and have no internet access as a consequence. The only way to transfer files to/from UPPMAX is through the 'wharf'. You can mount the wharf in your local file system with sshfs:

.. code-block:: shell

   mkdir wharf
   sshfs [userid]@bianca-sftp.uppmax.uu.se:[projectid]/[userid] wharf

If you are using the ``server``, the wharf is mounted at startup.

Running pipelines
------------------

Sensible SBATCH settings
^^^^^^^^^^^^^^^^^^^^^^^^
* ``freesurfer`` with a full run on one T1w (1x1x1mm) took 6h and used a maximum of 1 CPU
* ``fmriprep`` including ``freesurfer`` preprocessing on one functional run (3x3x3mm) and one T1w (1x1x1mm) took 5.5h and used a maximum of 8/8 CPUs (4 CPUs on average)
* ``qsiprep`` with output resolution 2mm on dwi data with one shell, 60 directions (3x3x3mm) took 3.25h and consumed a maximum of 8/8 CPUs (60% of the time), 6 CPUs on average

:func:`run_bidsapp`

## HCP pipeline using SLURM to run containerized pipelines on BIDS prepared datasets

Run single pipeline: 
`python3 run_bidsapp.py path/to/bids/dataset config_file.json`

Run a workflow of pipelines:
`python3 rub_batch.py path/to/bids/dataset workflow.json`

To build singularity containers run e.g. `singularity build fmriprep-23.2.3.simg docker://nipreps/fmriprep:23.2.3`

The relevant images are:

- MRIQC:     docker:/nipreps/mriqc
- fMRIPrep:  docker://nipreps/fmriprep
- XCP-D:     docker://pennlinc/xcp_d
- QSIPrep:   docker://pennbbl/qsiprep


Other images that could be added:

- docker://pennlinc/aslprep
- docker://bids/pyMVPA         (run on fMRIPrep output)
- docker://trends/gift-bids    (performs group ICA on fMRI data)
- docker://poldracklab/fitlins (GLM on fMRIPrep data - still maintained? Maybe use nilearn instead?)

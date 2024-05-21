#!/bin/bash

if [ $# -eq 0 ]; then
    echo "You need to specify a bids folder."
    exit 1
fi

STUDY=$1
PARTICIPANT_FILE=${STUDY}/data/participants.tsv

if [ ! -f ${PARTICIPANT_FILE} ]; then
    echo "$STUDY does not seem to be a valid bids project."
    exit 1
fi

MRIQC_CONTAINER=mriqc-23.1.1.fix
FMRIPREP_CONTAINER=fmriprep-23.2.0
QSIPREP_CONTAINER=qsiprep-0.20.0
XCPD_CONTAINER=xcp_d-0.6.1

#Globals for sbatch and singularity:
export BIDS_DIR="${STUDY}/data"
export APPTAINERENV_FS_LICENSE="/sw/apps/freesurfer/6.0.0/bianca/license.txt"
export APPTAINERENV_TEMPLATEFLOW_HOME="/templateflow"
# TMPDIR is defined by UPPMAX (deleted when job is finished)

PROJECT_NAME=$( echo $HOSTNAME | sed 's/-.*//' )
FMRIPREP_DIR="derivatives/fmriprep-23.2.0"
FREESURFER_DIR="${FMRIPREP_DIR}/sourcedata/freesurfer"
CONTAINER_DIR="/proj/$PROJECT_NAME/bidsflow"
TEMPLATEFLOW_HOST_HOME="${CONTAINER_DIR}/templateflow"

# The job array will be based on the number of participants defined in the BIDS dataset:
NSUBS=$(( $( wc -l ${PARTICIPANT_FILE} | cut -f1 -d' ' ) - 1 ))
echo "Found participant file with $NSUBS participants."
   

# Build command lines for SLURM -> Singularity -> BIDSApp:

SBATCH_CMD="sbatch --parsable \
                   --account $PROJECT_NAME \
                   --array=1-$NSUBS \
                   --time=24:00:00 \
                   -n 1 \
                   -p core \
                   --cpus-per-task=16 \
                   --mem-per-cpu=4G \
                   -o ${HOME}/log/%x-%A-%a.out \
                   -e ${HOME}/log/%x-%A-%a.err"

SINGULARITY_CMD="singularity run \
                --cleanenv \
                -B ${BIDS_DIR}:/data \
                -B ${TEMPLATEFLOW_HOST_HOME}:${APPTAINERENV_TEMPLATEFLOW_HOME} \
                -B ${TMPDIR}:/work"

MRIQC_CMD="${SINGULARITY_CMD} ${CONTAINER_DIR}/${MRIQC_CONTAINER}.simg /data /data/derivatives/${MRIQC_CONTAINER} participant \
	      -w /work \
	      -vv \
	      --omp-nthreads 8 \
	      --mem 30"
 
FMRIPREP_CMD="${SINGULARITY_CMD} ${CONTAINER_DIR}/${FMRIPREP_CONTAINER}.simg /data /data/derivatives/${FMRIPREP_CONTAINER} participant \
              -w /work/ \
              -vv \
              --omp-nthreads 8 \
              --mem 30 \
              --skip_bids_validation"

QSIPREP_CMD="${SINGULARITY_CMD} ${CONTAINER_DIR}/${QSIPREP_CONTAINER}.simg /data /data/derivatives/${QSIPREP_CONTAINER} participant \
             -w /work/ \
             -vv \
             --omp-nthreads 8 \
             --nthreads 8 \
             --mem_mb 30000 \
             --skip_bids_validation \
             --freesurfer_input=/data/${FREESURFER_DIR} \
             --use-syn-sdc \
             --recon-spec mrtrix_singleshell_ss3t_ACT-hsvs \
	     --output-resolution 1.2"

XCPD_CMD="${SINGULARITY_CMD} ${CONTAINER_DIR}/${XCPD_CONTAINER}.simg /data/${FMRIPREP_DIR} /data/derivatives/${XCPD_CONTAINER} participant \
          -w /work/ \
          -vv \
          --nthreads 8 \
          --omp-nthreads 8 \
          --mem_gb 30 \
          --input-type fmriprep \
          --fs-license-file=${APPTAINERENV_FS_LICENSE}"


# Submit SLURM job arrays, with dependencies between pipelines as needed:

MRIQC_ID=$(${SBATCH_CMD} --job-name ${MRIQC_CONTAINER} ./submit_job.sbatch ${MRIQC_CONTAINER} ${MRIQC_CMD})
echo "MRIQC job submitted: $MRIQC_ID"

FMRIPREP_ID=$(${SBATCH_CMD} --job-name ${FMRIPREP_CONTAINER} ./submit_job.sbatch ${FMRIPREP_CONTAINER} ${FMRIPREP_CMD})
echo "fMRIPrep job submitted: $FMRIPREP_ID"

#The following uses freesurfer and will not run until fMRIPrep is finished:

XCPD_ID=$(${SBATCH_CMD} -d aftercorr:$FMRIPREP_ID --job-name ${XCPD_CONTAINER} ./submit_job.sbatch ${XCPD_CONTAINER} ${XCPD_CMD})
echo "XCP-D job submitted: $XCPD_ID"

QSIPREP_ID=$(${SBATCH_CMD} -d aftercorr:$FMRIPREP_ID --job-name ${QSIPREP_CONTAINER} ./submit_job.sbatch ${QSIPREP_CONTAINER} ${QSIPREP_CMD})
echo "QSIPrep job submitted: $QSIPREP_ID"

#!/bin/bash

CONTAINER=$1
RUN_CMD="${@:2}"

mkdir -p ${BIDS_DIR}/derivatives/${CONTAINER}

# Parse the participants.tsv file and extract one subject ID from the line corresponding to this SLURM task.
subject=$( sed -n -E "$((${SLURM_ARRAY_TASK_ID} + 1))s/sub-(\S*)\>.*/\1/gp" ${BIDS_DIR}/participants.tsv )

CMD="${RUN_CMD} --participant-label $subject"

if [[ $(find ${BIDS_DIR}/derivatives/${CONTAINER} -name sub-$subject | wc -l) -gt 0 ]]; then
   echo "The pipeline ${CONTAINER} has already been run for $subject."
   exitcode=0
else
   echo Running task ${SLURM_ARRAY_TASK_ID}
   echo Commandline: ${CMD}
   eval ${CMD}
   exitcode=$?

   # Output results to a table
   echo "sub-$subject   ${SLURM_ARRAY_TASK_ID}    $exitcode" \
      >> ${SLURM_JOB_NAME}.${SLURM_ARRAY_JOB_ID}.tsv
   echo Finished tasks ${SLURM_ARRAY_TASK_ID} with exit code $exitcode
fi
exit $exitcode

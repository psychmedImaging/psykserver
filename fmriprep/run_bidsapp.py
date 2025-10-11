#The user needs to provide 
#    -a path to a project folder, containing the subfolder 'data' with a (valid) bids project, including a participants.tsv within
#     (All participants in data/participants.tsv will be processed)
#    -a config json file (the script will look for it in the root of the project folder
#    -if depend_job is set to a job id, the current job will not start until the job corresponding to the id is finished

import os, subprocess, argparse, datetime, json, glob, io, csv

def run_bidsapp(study_folder,config_file,depend_job=None):
    
    #set up paths etc
    project_name=os.environ['HOSTNAME'].split('-')[0]
    current_folder='/proj/sens2019025/bidsflow'#os.path.dirname(os.path.realpath(__file__))
    container_folder=os.path.join(current_folder,'containers')
    templateflow_folder=os.path.join(current_folder,'templateflow')
    bids_folder=os.path.join(study_folder,'data')
    config_path=os.path.join(study_folder,config_file)
    
    #get settings from config file
    with open(config_path) as f:
        cfg=json.load(f)
    option_string=' '.join(x + ' ' + y for x, y in cfg['options'].items())
    container=cfg['container']
    container_file=os.path.join(container_folder,container)
    if 'job-name' in cfg:
        job_name=cfg['job-name']
    else:
        job_name=os.path.splitext(container_file)[0]
    input_folder=cfg['input-data']
    log_folder=os.path.join(study_folder,'logs',job_name+'_'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    os.makedirs(log_folder,exist_ok=True)
    if 'environment' in cfg:
        for key,val in cfg['environment'].items():
            os.environ[key] = val
    if 'sbatch' in cfg:
        timelimit=cfg['sbatch']['timelimit']
        ntasks=cfg['sbatch']['ntasks']
    
    #clean up non-finished freesurfer runs
    freesurfer_folder=os.path.join(bids_folder,'derivatives',container_file,'sourcedata','freesurfer')
    if os.path.exists(freesurfer_folder):
        for f in glob.glob(os.path.join(freesurfer_folder,'*/scripts/*Running*')):
            os.remove(f)
    
    #get participants to process
    participants=get_participants(bids_folder)
    array='1-'+str(len(participants))
    
    #build the bidsapp command and send to sbatch:
    bidsapp_cmd='subject="$(cut -d" " -f$SLURM_ARRAY_TASK_ID <<<'+'"'+(' '.join(participants))+'")"\n \
                 singularity run \
                     --cleanenv \
                     -B '+bids_folder+':/data \
                     -B '+templateflow_folder+':/templateflow \
                     -B '+os.environ['TMPDIR']+':/work '+ \
                     container_file+' '+input_folder+' /data/derivatives/'+job_name+' participant \
                         --participant-label $subject '+ \
                         option_string+'\n \
                 exitcode=$?\n \
                 echo "$subject\t$SLURM_ARRAY_JOB_ID_$SLURM_ARRAY_TASK_ID\t$exitcode" >> '+os.path.join(log_folder,job_name+'_log.tsv')

    jobid=sbatch(job_name,project_name,array,os.path.join(log_folder,'%A-%a'),bidsapp_cmd,timelimit,ntasks,depend_job)

    #build and run command for logging resource usage:
    jobstats_cmd='sleep 30\n \
                  cd '+log_folder+'\n \
                  sacct --format="jobid,state,start,elapsed,ncpus,cputime,totalcpu,reqmem,maxrss,exitcode" -j '+jobid+' --parsable2 | column -s "|" -t > '+job_name+'_jobstats.txt\n \
                  jobstats -p '+jobid
    
    sbatch('jobstats',project_name,0,os.path.join(log_folder,'%A'),jobstats_cmd,5,1,jobid)
    print('Submitted sbatch job '+jobid+'\n \
               \tContainer\t'+os.path.basename(container_file)+'\n \
               \tProject folder\t'+study_folder+'\n \
               \tConfig file\t'+config_path+'\n \
               \t# participants\t'+str(len(participants)))
    return jobid

def sbatch(job_name,proj_name,array,log,command,time,threads,dependency):
    sbatch_cmd = "sbatch --parsable -J {} -A {} -a {} -t {} -n {} -o {}.out -e {}.err --wrap='{}'".format(job_name,proj_name,array,time,threads,log,log,command)
    if dependency is not None:
        sbatch_cmd+=' -d afterok:'+dependency
    return subprocess.getoutput(sbatch_cmd)

def get_participants(folder):
    file=os.path.join(folder,'participants.tsv')
    if not os.path.exists(file):
        raise Exception('No participants.tsv found in '+folder)
    participants=[]
    with io.open(file,'r',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f,delimiter='\t')
        for row in reader:
            participants.append(row['participant_id'])
    return participants

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='run-bidsapp')
    parser.add_argument('path')
    parser.add_argument('config')
    args=parser.parse_args()
    run_bidsapp(args.path,args.config)

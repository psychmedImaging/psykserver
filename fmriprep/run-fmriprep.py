#The user needs to provide a path to [basefolder], containing the subfolder 'data' with a (valid) bids project, including a participants.tsv within
#All participants in data/participants.tsv will be processed
#The script looks for *_config.json in [basefolder]. If not present, default settings are used.

import os, subprocess, argparse, csv, io, datetime, json
from sbatch import sbatch

projectName=os.environ['HOSTNAME'].split('-')[0]
currentFolder=os.path.realpath(__file__)
containerFolder=os.path.join(currentFolder,'containers')
templateflowFolder=os.path.join(currentFolder,'templateflow')
os.environ['APPTAINERENV_FS_LICENSE'] = '/sw/apps/freesurfer/7.4.1/bianca/license.txt'
os.environ['APPTAINERENV_TEMPLATEFLOW_HOME'] ='/templateflow'

#read arguments and set up paths
parser = argparse.ArgumentParser(prog='run-fmriprep')
parser.add_argument('path')
parser.add_argument('-c', '--config-file',required=False,default='fmriprep-default.json')
args=parser.parse_args()
studyFolder=args.path
bidsFolder=os.path.join(studyFolder,'data')
configFile=args.config_file

#get settings from config file
configPath=os.path.join(studyFolder,configFile)
if not os.path.exists(configPath):
    configPath=os.path.join(currentFolder,configFile)
with open(configPath) as f:
    cfg=json.load(f)
    cfgString=' '.join(x + ' ' + y for x, y in cfg['options'].items())
containerFile='fmriprep-'+cfg['version']
logFolder=os.path.join(studyFolder,'logs',containerFile+'_'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
outputFolder=os.path.join(studyFolder,'derivatives',containerFile)
os.makedirs(logFolder,exist_ok=True)
os.makedirs(outputFolder,exist_ok=True)

#get participants to process
participantFile=os.path.join(bidsFolder,'participants.tsv')
if not os.path.exists(participantFile):
    raise Exception('No participants.tsv found in '+bidsFolder)
participants=[]
with io.open(participantFile,'r',encoding='utf-8-sig') as file:
    reader=csv.DictReader(file,delimiter='\t')
    for row in reader:
        participants.append(row['participant_id'])
array='1-'+str(len(participants))


#build the command to send to sbatch:
getsubjectCommand='subject="$(cut -d" " -f$SLURM_ARRAY_TASK_ID <<<'+'"'+(' '.join(participants))+'")"'
logCommand='exitcode=$?\necho "$subject\t$SLURM_ARRAY_TASK_ID\t$exitcode" >> '+os.path.join(logFolder,containerFile+'.tsv')
singularityCommand='singularity run --cleanenv -B '+bidsFolder+':/data -B '+templateflowFolder+':/templateflow -B '+os.environ['TMPDIR']+':/work'
fmriprepCommand=os.path.join(containerFolder,containerFile)+'.simg /data /data/derivatives/'+containerFile+' participant --participant-label $subject '+cfgString
fullCommand=getsubjectCommand+'\n'+singularityCommand+' '+fmriprepCommand+'\n'+logCommand

#submit the job array to sbatch:
sbatch(containerFile,projectName,array,os.path.join(logFolder,'%A-%a'),fullCommand)
print('\tContainer\t'+os.path.basename(containerFile)+'\n\tProject folder\t'+studyFolder+'\n\tConfig file\t'+configPath+'\n\t# participants\t'+str(len(participants)))

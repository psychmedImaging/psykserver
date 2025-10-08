#The user needs to provide a path to [basefolder], containing the subfolder 'data' with a (valid) bids project, including a participants.tsv within
#All participants in data/participants.tsv will be processed
#The script looks for *_config.json in [basefolder]. If not present, default settings are used.

import os, subprocess, argparse, datetime, json
from sbatch import sbatch
from sbatch import get_participants

projectName=os.environ['HOSTNAME'].split('-')[0]
currentFolder=os.path.realpath(__file__)
containerFolder=os.path.join(currentFolder,'containers')
templateflowFolder=os.path.join(currentFolder,'templateflow')

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
optionString=' '.join(x + ' ' + y for x, y in cfg['options'].items())
containerFile=cfg['container']
logFolder=os.path.join(studyFolder,'logs',containerFile+'_'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
os.makedirs(logFolder,exist_ok=True)
for key,val in cfg['environment'].items():
    os.environ[key] = val

#get participants to process
participants=get_participants(bidsFolder)
array='1-'+str(len(participants))

#build the command to send to sbatch:
getsubjectCommand='subject="$(cut -d" " -f$SLURM_ARRAY_TASK_ID <<<'+'"'+(' '.join(participants))+'")"'
logCommand='exitcode=$?\necho "$subject\t$SLURM_ARRAY_TASK_ID\t$exitcode" >> '+os.path.join(logFolder,containerFile+'.tsv')
singularityCommand='singularity run --cleanenv -B '+bidsFolder+':/data -B '+templateflowFolder+':/templateflow -B '+os.environ['TMPDIR']+':/work'
bidsappCommand=os.path.join(containerFolder,containerFile)+'.simg /data /data/derivatives/'+containerFile+' participant --participant-label $subject '+optionString
fullCommand=getsubjectCommand+'\n'+singularityCommand+' '+bidsappCommand+'\n'+logCommand

#submit the job array to sbatch:
jobid=sbatch(containerFile,projectName,'11',os.path.join(logFolder,'%A-%a'),fullCommand)
os.system('cd '+logFolder+' & jobstats --plot -r '+jobid)
print('Submitted sbatch job '+jobid+'\n\tContainer\t'+os.path.basename(containerFile)+'\n\tProject folder\t'+studyFolder+'\n\tConfig file\t'+configPath+'\n\t# participants\t'+str(len(participants)))

import subprocess, os, io, csv
def sbatch(job_name,proj_name,array,log,command,time='24:00:00',threads='8'):
    sbatch_command = "sbatch --parsable -J {} -A {} -a {} -t {} -n {} -o {}.out -e {}.err --wrap='{}'".format(job_name,proj_name,array,time,threads,log,log,command)
    return subprocess.getoutput(sbatch_command)

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

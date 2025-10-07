import subprocess
def sbatch(job_name,proj_name,array,log,command,time='24:00:00',threads='8'):
    sbatch_command = "sbatch -J {} -A {} -a {} -t {} -n {} -o {}.out -e {}.err --wrap='{}'".format(job_name,proj_name,array,time,threads,log,log,command)
    print(sbatch_command)
    sbatch_response = subprocess.getoutput(sbatch_command)
    print(sbatch_response)

import os, json, argparse
from run_bidsapp import run_bidsapp

parser = argparse.ArgumentParser(prog='run-batch')
parser.add_argument('path')
parser.add_argument('config')
args=parser.parse_args()

study_folder=args.path
config_file=os.path.join(study_folder,args.config)

jobids=[]
with open(config_file) as f:
    cfg=json.load(f)
for job in cfg:
    job_file=os.path.join(study_folder,job['config'])
    depend_job=None
    dependency=job['dependency']
    if dependency is not None:
        depend_job='afterok:'+jobids[dependency]
    jobids.append(run_bidsapp(study_folder,job_file,depend_job))

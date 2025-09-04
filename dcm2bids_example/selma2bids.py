import os, sys, shutil, json, glob, subprocess
import dcm2bids, spec2nii, pydicom

#args

if len(sys.argv) < 3:
    raise Exception('Expected 3 arguments (input dir, output dir, subject id)')
indir=sys.argv[1]
outdir=sys.argv[2]
subject=sys.argv[3]

config_file=os.path.join(os.path.dirname(os.path.realpath(__file__)),'config.json')
dcm_folder=os.path.join(indir,'DICOM')
spec_folder=os.path.join(indir,'spectra_dcm')
pattern='sub-'+subject
bids_folder=os.path.join(outdir,pattern)

subprocess.call(['dcm2bids', '-d', dcm_folder, '-p', subject, '-c',config_file, '-o',outdir])

#do some post-conversion cleanups
def fix_sidecar(f,p):
    with open(f,'r') as jfile:
        j=json.loads(jfile.read())
    j['PhaseEncodingDirection']=p
    j['EffectiveEchoSpacing']=j['EstimatedEffectiveEchoSpacing']
    j['TotalReadoutTime']=j['EstimatedTotalReadoutTime']
    with open(f,'w') as jfile:
        jfile.write(json.dumps(j, indent=4))

fmap_folder=os.path.join(bids_folder,'fmap')
func_folder=os.path.join(bids_folder,'func')
dwi_folder=os.path.join(bids_folder,'dwi')

funcjson=os.path.join(func_folder,pattern+'_task-rest_bold.json')

#add phase encoding direction and readout time to sidecars
fix_sidecar(os.path.join(fmap_folder,pattern+'_acq-rest_dir-AP_epi.json'),'j-')
fix_sidecar(os.path.join(fmap_folder,pattern+'_acq-rest_dir-PA_epi.json'),'j')
fix_sidecar(os.path.join(fmap_folder,pattern+'_acq-MSIT_dir-AP_epi.json'),'j-')
fix_sidecar(os.path.join(fmap_folder,pattern+'_acq-MSIT_dir-PA_epi.json'),'j')
fix_sidecar(funcjson,'j')
fix_sidecar(os.path.join(fmap_folder,pattern+'_acq-dwi_dir-AP_epi.json'),'j-')
fix_sidecar(os.path.join(dwi_folder,pattern+'_dir-PA_dwi.json'),'j')

#Remove conflicting json entry
with open(funcjson,'r') as jfile:
    j=json.loads(jfile.read())
del j['AcquisitionDuration']
with open(funcjson,'w') as jfile:
    jfile.write(json.dumps(j, indent=4))


#remove bval/bvec for DTI fmap
for f in glob.glob(os.path.join(fmap_folder,'*.bv*')):
    os.remove(f)

#remove temporary files
shutil.rmtree(os.path.join(outdir,'tmp_dcm2bids'))

#collect dicom spectras, sort them, convert to nifti/json and rename to bids
spec_tmp_folder=os.path.join(bids_folder,'spectmp')
mrs_folder=os.path.join(bids_folder,'mrs')
os.makedirs(mrs_folder,exist_ok=True)

#collect and sort dicoms
files=glob.glob(os.path.join(spec_folder,'**','XX*'),recursive=True)

for f in files:
    ds=pydicom.dcmread(f,force=True)
    if (0x2005,0x1313) in ds:
        outfolder=os.path.join(spec_tmp_folder,ds[0x0008,0x103E].value)
        os.makedirs(outfolder,exist_ok=True)
        shutil.copy(f,os.path.join(outfolder,str(ds[0x2005,0x1313].value)+'.dcm'))

#dcm2nii conversion
dirs=glob.glob(os.path.join(spec_tmp_folder,'MEGA*'))
for d in dirs:
    bname=os.path.basename(d)
    subprocess.call(['spec2nii','philips_dcm','-j','-f', bname+'_act', '-o', spec_tmp_folder, os.path.join(spec_tmp_folder,d,'1.dcm')])
    subprocess.call(['spec2nii','philips_dcm','-j','-f', bname+'_ref', '-o', spec_tmp_folder, os.path.join(spec_tmp_folder,d,'2.dcm')])
    #bids renaming
    voxel=d.split('_')[2]
    specname=pattern+'_acq-mega-press_nuc-1H_voi-'+voxel
    svsname=specname+'_svs'
    refname=specname+'_mrsref'
    os.rename(os.path.join(spec_tmp_folder,bname+'_act.nii.gz'),os.path.join(mrs_folder,svsname+'.nii.gz'))
    os.rename(os.path.join(spec_tmp_folder,bname+'_act.json'),os.path.join(mrs_folder,svsname+'.json'))
    os.rename(os.path.join(spec_tmp_folder,bname+'_ref.nii.gz'),os.path.join(mrs_folder,refname+'.nii.gz'))
    os.rename(os.path.join(spec_tmp_folder,bname+'_ref.json'),os.path.join(mrs_folder,refname+'.json'))

#shutil.rmtree(spec_tmp_folder)
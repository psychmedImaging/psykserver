%User defined:
sess={'ses-baseline'};  %List of sessions to process
root_folder = '\\argos.rudbeck.uu.se\mygroups$\Gold\Brian';
data_folder = fullfile(root_folder,'projects_ongoing\AVH_SMA\bidsdata');
outputFolder = fullfile(data_folder, 'derivatives\osprey_2023-11-12_avh_megapress');


seqType                     = 'MEGA';
editTarget                  = {'GABA'};
dataScenario                = 'invivo';
opts.SpecReg                = 'ProbSpecReg';    %This performed better than default with our data (Brian/AVH)
opts.SubSpecAlignment.mets  = 'L2Norm';

%eddy current correction:
opts.ECC.raw                = 1;
opts.ECC.mm                 = 1;

%output options:
opts.saveLCM                = 0;
opts.savejMRUI              = 0;
opts.saveVendor             = 0;
opts.saveNII                = 0;
opts.savePDF                = 0;

opts.fit.includeMetabs      = {'default'};
opts.fit.method             = 'Osprey';
opts.fit.style              = 'Separate';
opts.fit.range              = [0.5 4];
opts.fit.rangeWater         = [2.0 7.4];
opts.fit.bLineKnotSpace     = 0.55;             %Choosen according to Zöllner et al., 2022
opts.fit.fitMM              = 1;
%Had to set this manually for some reason but should be auto detected:
opts.fit.basisSetFile       = 'C:\Users\Jonpe389\Documents\MATLAB\Osprey\osprey-develop\fit\basissets\3T\philips\mega\press\gaba68\basis_philips_megapress_gaba68.mat';
opts.fit.coMM3              = '3to2MM';
opts.fit.FWHMcoMM3          = 14;

opts.img.deface             = 0;

clear files files_ref files_w files_nii files_mm

subs=dir(fullfile(data_folder,'sub-*'));
counter=0;
subcnt=0;

for kk = 1:length(subs)
    subdir=fullfile(subs(kk).folder,subs(kk).name);
    for ll = 1:length(sess)
        sesdir=fullfile(subdir,sess{ll});
        metfile=fullfile(sesdir,'mrs',[subs(kk).name '_' sess{ll} '_acq-megapress_nuc-1H_voi-dACC_svs.nii.gz']);
        reffile=fullfile(sesdir,'mrs',[subs(kk).name '_' sess{ll} '_acq-megapress_nuc-1H_voi-dACC_ref.nii.gz']);
        if exist(metfile,'file') && exist(reffile,'file')
            counter=counter+1;
            if ll==1;subcnt=subcnt+1;end
            files(counter)={metfile};
            files_ref(counter)={reffile};
            files_w     = {}; %no water data w short te
            files_mm     = {}; %no metabolite nulled data
            anatfile=fullfile(sesdir,'anat',[subs(kk).name '_' sess{ll} '_T1w.nii.gz']);
            files_nii(counter)  = {anatfile};
            if startsWith(subs(kk).name,'sub-avh2')
                group=2;
            elseif startsWith(subs(kk).name,'sub-avh1')
                group=1;
            elseif startsWith(subs(kk).name,'sub-avh3')
                group=3;
            end
        end
    end
end

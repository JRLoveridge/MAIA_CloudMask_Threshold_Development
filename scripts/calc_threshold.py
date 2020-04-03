import numpy as np
import h5py
from scipy.stats import cumfreq

def calc_thresh(group_file):
    '''
    Objective:
        Takes in grouped_obs_and_CM.hdf5 file. Inside are a datasets for
        a bin and inside are rows containing the cloud mask and
        observables for each pixel. The OLP is in the dataset name. The
        threshold is then calculated for that dataset and saved into a
        threshold file.
    Arguments:
        group_file {str} -- contains data points to calc threshold for
        all bins in the file
    Return:
        void
    '''
    home = '/data/keeling/a/vllgsbr2/c/old_MAIA_Threshold_dev/LA_PTA_MODIS_Data/try2_database/'
    with h5py.File(group_file, 'r+') as hf_group,\
         h5py.File(home + '/thresholds_MCM_efficient.hdf5', 'w') as hf_thresh:

        #cosSZA_00_VZA_00_RAZ_00_TA_00_sceneID_00_DOY_00
        TA_group  = hf_thresh.create_group('TA_bin_01')#bin_ID[24:29])
        DOY_group = TA_group.create_group('DOY_bin_06')#bin_ID[-6:])

        master_thresholds = np.ones((10*14*12*21)).reshape((10,14,12,21))*-999
        obs_names = ['WI', 'NDVI', 'NDSI', 'VIS_Ref', 'NIR_Ref', 'SVI', 'Cirrus']
        for obs in obs_names:
            DOY_group.create_dataset(obs, data=master_thresholds)

        hf_keys    = list(hf_group.keys())
        num_points = len(hf_keys)

        for count, bin_ID in enumerate(hf_keys):
            #location in array to store threshold (cos(SZA), VZA, RAZ, Scene_ID)
            bin_idx = [int(bin_ID[7:9]), int(bin_ID[14:16]), int(bin_ID[21:23]), int(bin_ID[38:40])]

            cloud_mask = hf_group[bin_ID][:,0].astype(dtype=np.int)
            obs        = hf_group[bin_ID][:,1:]
            #print(cloud_mask)
            clear_idx = np.where(cloud_mask != 0)
            clear_obs = obs[clear_idx[0],:]
            #print(clear_idx[0].shape)
            cloudy_idx = np.where(cloud_mask == 0)
            cloudy_obs = obs[cloudy_idx[0],1:3] #[1:3] since we only need for NDxI
            #print(cloudy_idx[0].shape)
            for i in range(7):
                thresh_nan = False
                #path to TA/DOY/obs threshold dataset
                path = '{}/{}/{}'.format('TA_bin_01', 'DOY_bin_06', obs_names[i])
                
                #WI
                if i==0:
                    hf_thresh[path][bin_idx[0], bin_idx[1], bin_idx[2], bin_idx[3]] = \
                    np.nanpercentile(clear_obs[:,i], 1)
                #NDxI
                #pick max from cloudy hist
                elif i==1 or i==2:
                    hist, bin_edges = np.histogram(cloudy_obs[:,i-1], bins=128, range=(-1,1))
                    if i==2:
                        print(hist.sum()) 
                    hf_thresh[path][bin_idx[0], bin_idx[1], bin_idx[2], bin_idx[3]] =\
                    bin_edges[1:][hist==hist.max()].min()
                #VIS/NIR/SVI/Cirrus
                else:
                    hf_thresh[path][bin_idx[0], bin_idx[1], bin_idx[2], bin_idx[3]] =\
                    np.nanpercentile(clear_obs[:,i], 99)
                
                if np.isnan(hf_thresh[path][bin_idx[0], bin_idx[1], bin_idx[2], bin_idx[3]]):
                    thresh_nan = True   
                    #print('{} | threshold: {:1.4f} | clear_obs: {} cloudy_obs: {}'.format(bin_ID, hf_thresh[path][bin_idx[0], bin_idx[1], bin_idx[2], bin_idx[3]], clear_obs, cloudy_obs))

if __name__ == '__main__':

    import h5py
    import tables
    import os
    tables.file._open_files.close_all()

    #define paths for the database
    home = '/data/keeling/a/vllgsbr2/c/old_MAIA_Threshold_dev/LA_PTA_MODIS_Data/try2_database/'
    grouped_file_path    = home + 'grouped_obs_and_CM.hdf5'

    calc_thresh(grouped_file_path)


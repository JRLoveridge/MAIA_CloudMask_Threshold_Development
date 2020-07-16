import numpy as np
import h5py

def calc_thresh(thresh_home, group_file, DOY_bin, TA):
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

    DOY_end = (DOY_bin+1)*8
    DOY_start = DOY_end - 7
    home = '/data/keeling/a/vllgsbr2/c/old_MAIA_Threshold_dev/LA_PTA_MODIS_Data/try2_database/'
    with h5py.File(group_file, 'r') as hf_group,\
         h5py.File(thresh_home + '/thresholds_DOY_{:03d}_to_{:03d}_bin_{:02d}.h5'.format(DOY_start, DOY_end, DOY_bin), 'w') as hf_thresh:

        #cosSZA_00_VZA_00_RAZ_00_TA_00_sceneID_00_DOY_00
        TA_group  = hf_thresh.create_group('TA_bin_{:02d}'.format(TA))#bin_ID[24:29])
        DOY_group = TA_group.create_group('DOY_bin_{:02d}'.format(DOY_bin))#bin_ID[-6:])

        num_sfc_types = 15

        master_thresholds = np.ones((10*15*12*num_sfc_types)).reshape((10,15,12,num_sfc_types))*-999
        obs_names = ['WI', 'NDVI', 'NDSI', 'VIS_Ref', 'NIR_Ref', 'SVI', 'Cirrus']
        for obs in obs_names:
            DOY_group.create_dataset(obs, data=master_thresholds)

        hf_keys    = list(hf_group.keys())
        num_points = len(hf_keys)

        for count, bin_ID in enumerate(hf_keys):
            # print(count, bin_ID)
            #location in array to store threshold (cos(SZA), VZA, RAZ, Scene_ID)
            bin_idx = [int(bin_ID[7:9]), int(bin_ID[14:16]), int(bin_ID[21:23]), int(bin_ID[38:40])]

            cloud_mask = hf_group[bin_ID][:,0].astype(dtype=np.int)
            obs        = hf_group[bin_ID][:,1:]
            #print(cloud_mask)
            clear_idx = np.where(cloud_mask != 0)
            clear_obs = obs[clear_idx[0],:]
            cloudy_idx = np.where(cloud_mask == 0)
            cloudy_obs = obs[cloudy_idx[0],:]
            print(cloudy_idx[0].shape)
            for i in range(7):
                #thresh_nan = False
                #path to TA/DOY/obs threshold dataset
                path = '{}/{}/{}'.format('TA_bin_{:02d}', 'DOY_bin_{:02d}'.format(TA, DOY_bin), obs_names[i])

                # print(clear_obs[:,i])
                #WI
                if i==0:
                    if clear_obs[:,i].shape[0] > 0:
                        hf_thresh[path][bin_idx[0], bin_idx[1], bin_idx[2], bin_idx[3]] = \
                        np.nanpercentile(clear_obs[:,i], 1)

                    #choose least white cloudy pixel as threshold if no clear obs
                    else:
                        hf_thresh[path][bin_idx[0], bin_idx[1], bin_idx[2], bin_idx[3]] = \
                        cloudy_obs[:, i].max()

                #NDxI
                #pick max from cloudy hist
                elif i==1 or i==2:
                    if cloudy_obs[:,i].shape[0] > 0:
                        hist, bin_edges = np.histogram(cloudy_obs[:,i], bins=128, range=(-1,1))
                        hf_thresh[path][bin_idx[0], bin_idx[1], bin_idx[2], bin_idx[3]] =\
                        bin_edges[1:][hist==hist.max()].min()
                    #set default value of 1e-3 if no cloudy obs available
                    else:
                        hf_thresh[path][bin_idx[0], bin_idx[1], bin_idx[2], bin_idx[3]] = 1e-3
                #VIS/NIR/SVI/Cirrus
                else:
                    if clear_obs[:,i].shape[0] > 0:
                        x = np.array(clear_obs[:,i])
                        hf_thresh[path][bin_idx[0], bin_idx[1], bin_idx[2], bin_idx[3]] =\
                        np.nanpercentile(x, 99)

                    else:
                        hf_thresh[path][bin_idx[0], bin_idx[1], bin_idx[2], bin_idx[3]] =\
                        cloudy_obs[:, i].min()

                if hf_thresh[path][bin_idx[0], bin_idx[1], bin_idx[2], bin_idx[3]] == -999:
                    print('binID: {} | obs#: {}'.format(bin_ID, i))

                #if np.isnan(hf_thresh[path][bin_idx[0], bin_idx[1], bin_idx[2], bin_idx[3]]):
                #    thresh_nan = True
                    #if there isn't enough clear or cloudy obs, assign value to make threshold true
                    #if no clear, and need clear, assign threshold as least brightest cloudy
                    #if no cloudy, and need cloudy, assign thresholds as 1e-3 (NDxI)
                   # print('{} | threshold: {:1.4f} | clear_obs: {} cloudy_obs: {}'.format(bin_ID, hf_thresh[path][bin_idx[0], bin_idx[1], bin_idx[2], bin_idx[3]], clear_obs, cloudy_obs))

if __name__ == '__main__':

    import h5py
    # import tables
    import os
    import mpi4py.MPI as MPI
    import sys
    import configparser
    # tables.file._open_files.close_all()

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    for r in range(size):
        if rank==r:

            config_home_path = '/data/keeling/a/vllgsbr2/c/MAIA_thresh_dev/MAIA_CloudMask_Threshold_Development'
            config = configparser.ConfigParser()
            config.read(config_home_path+'/test_config.txt')

            PTA          = config['current PTA']['PTA']
            PTA_path     = config['PTAs'][PTA]
            TA           = int(config['Target Area Integer'][PTA])
            grouped_home = config['supporting directories']['combined_group']
            thresh_home  = config['supporting directories']['thresh']
            grouped_home = '{}/{}'.format(PTA_path, grouped_home)
            thresh_home  = '{}/{}'.format(PTA_path, thresh_home)

            #define paths for the database
            DOY_bin   = r
            DOY_end   = (DOY_bin+1)*8
            DOY_start = DOY_end - 7
            grouped_file_path = '{}/grouped_obs_and_CM_{:03d}_to_{:03d}_bin_{:02d}.h5'.\
                                format(grouped_home, DOY_start, DOY_end, DOY_bin)
            # print(grouped_file_path)
            calc_thresh(thresh_home, grouped_file_path, DOY_bin, TA)

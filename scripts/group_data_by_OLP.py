def make_sceneID(observable_level_parameter):

        """
        helper function to combine water/sunglint/snow-ice mask/sfc_ID into
        one mask. This way the threhsolds can be retrieved with less queries.
        [Section N/A]
        Arguments:
            observable_level_parameter {3D narray} -- return from func get_observable_level_parameter()
        Returns:
            2D narray -- scene ID. Values 0-28 inclusive are land types; values
                         29, 30, 31 are water, water with sun glint, snow/ice
                         respectively. Is the size of the granule. These integers
                         serve as the indicies to select a threshold based off
                         surface type.
        """
        # land_water_bins {2D narray} -- land (1) water(0)
        # sun_glint_bins {2D narray} -- no glint (1) sunglint (0)
        # snow_ice_bins {2D narray} -- no snow/ice (1) snow/ice (0)

        #over lay water/glint/snow_ice onto sfc_ID to create a scene_type_identifier
        land_water_bins = OLP[:,:, 4]
        sun_glint_bins  = OLP[:,:,-1]
        snow_ice_bins   = OLP[:,:, 5]

        sfc_ID_bins = observable_level_parameter[:,:,6]
        scene_type_identifier = sfc_ID_bins

        scene_type_identifier[ land_water_bins == 0]    = 30
        scene_type_identifier[(sun_glint_bins  == 1) & \
                              (land_water_bins == 0) ]  = 31
        scene_type_identifier[ snow_ice_bins   == 0]    = 32

        return scene_type_identifier

def group_data(OLP, obs, CM, time_stamp):
    """
    Objective:
        Group data by observable_level_paramter (OLP), such that all data in same
        group has a matching OLP. The data point is stored in the group with its
        observables, cloud mask, time stamp, and lat/lon. Will process one MAIA
        grid at a time. No return, will just be written to file in this function.
    Return:
        void
    """
    # observable_level_parameter = np.dstack((binned_cos_SZA ,\
    #                                         binned_VZA     ,\
    #                                         binned_RAZ     ,\
    #                                         Target_Area    ,\
    #                                         land_water_mask,\
    #                                         snow_ice_mask  ,\
    #                                         sfc_ID         ,\
    #                                         binned_DOY     ,\
    #                                         sun_glint_mask))

    #first make the scene ID and then use it to consolidate the OLP
    scene_ID = make_sceneID(OLP)

    new_OLP = np.zeros((1000,1000,6))
    new_OLP[:,:,:4] = OLP[:,:,:4] #cosSZA, VZA, RAZ, TA
    new_OLP[:,:,4]  = OLP[:,:,-2] #DOY
    new_OLP[:,:,5]  = scene_ID    #scene_ID

    #now for any OLP combo, make a group and save the data points into it
    for i in range(len(new_OLP)):
        for j in range(len(new_OLP[0])):
            if obs[i,j,0] >= 0.0:#negative fill values imply missing data so dont process it
                print('in loop ({},{})'.format(i,j))
                temp_OLP = new_OLP[i,j,:].astype(dtype=np.int)
                group = 'cosSZA_{:02d}_VZA_{:02d}_RAZ_{:02d}_TA_{:02d}_DOY_{:02d}_sceneID_{:02d}'\
                        .format(temp_OLP[0], temp_OLP[1], temp_OLP[2],\
                                temp_OLP[3], temp_OLP[4], temp_OLP[5])

                home = '/data/keeling/a/vllgsbr2/c/old_MAIA_Threshold_dev/LA_PTA_MODIS_Data/try2_database/'
                filename = '{}grouped_data_{}.hdf5'.format(home, group)

                try:#this is to write a new file and add data point
                    with h5py.File(filename, 'w') as hf_grouped_data:
                        data_pnt_group = hf_grouped_data.create_group('data_point_time_stamp_{}_i_{}_j_{}'\
                                                     .format(time_stamp, i, j))

                        data_pnt_group.create_dataset('cloud_mask', data=CM[i,j]   )
                        data_pnt_group.create_dataset('WI'        , data=obs[i,j,0])
                        data_pnt_group.create_dataset('NDVI'      , data=obs[i,j,1])
                        data_pnt_group.create_dataset('NDSI'      , data=obs[i,j,2])
                        data_pnt_group.create_dataset('visRef'    , data=obs[i,j,3])
                        data_pnt_group.create_dataset('nirRef'    , data=obs[i,j,4])
                        data_pnt_group.create_dataset('SVI'       , data=obs[i,j,5])
                        data_pnt_group.create_dataset('cirrus'    , data=obs[i,j,6])
                except:
                    try:#this is to add a data point to an existing file
                        with h5py.File(filename, 'r+') as hf_grouped_data:
                            data_pnt_group = hf_grouped_data.create_group('data_point_time_stamp_{}_i_{}_j_{}'\
                                                         .format(time_stamp, i, j))

                            data_pnt_group.create_dataset('cloud_mask', data=CM[i,j]   )
                            data_pnt_group.create_dataset('WI'        , data=obs[i,j,0])
                            data_pnt_group.create_dataset('NDVI'      , data=obs[i,j,1])
                            data_pnt_group.create_dataset('NDSI'      , data=obs[i,j,2])
                            data_pnt_group.create_dataset('visRef'    , data=obs[i,j,3])
                            data_pnt_group.create_dataset('nirRef'    , data=obs[i,j,4])
                            data_pnt_group.create_dataset('SVI'       , data=obs[i,j,5])
                            data_pnt_group.create_dataset('cirrus'    , data=obs[i,j,6])
                    except: #this is to overwrite the data point in an existing file
                        with h5py.File(filename, 'r+') as hf_grouped_data:
                            data_pnt_name = 'data_point_time_stamp_{}_i_{}_j_{}'\
                                            .format(time_stamp, i, j)
                            hf_grouped_data['{}/cloud_mask'.format(data_pnt_name) ][:] = CM[i,j]
                            hf_grouped_data['{}/WI'.format(data_pnt_name) ][:]         = obs[i,j,0]
                            hf_grouped_data['{}/NDVI'.format(data_pnt_name) ][:]       = obs[i,j,1]
                            hf_grouped_data['{}/NDSI'.format(data_pnt_name) ][:]       = obs[i,j,2]
                            hf_grouped_data['{}/visRef'.format(data_pnt_name) ][:]     = obs[i,j,3]
                            hf_grouped_data['{}/nirRef'.format(data_pnt_name) ][:]     = obs[i,j,4]
                            hf_grouped_data['{}/SVI'.format(data_pnt_name) ][:]        = obs[i,j,5]
                            hf_grouped_data['{}/cirrus'.format(data_pnt_name) ][:]     = obs[i,j,6]


if __name__ == '__main__':

    import numpy as np
    import h5py
    import mpi4py.MPI as MPI
    import tables
    import os
    tables.file._open_files.close_all()

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    for r in range(size):
        if rank==r:
            #define paths for the three databases
            PTA_file_path = '/data/keeling/a/vllgsbr2/c/old_MAIA_Threshold_dev/LA_PTA_MODIS_Data/try2_database/'
            database_files = os.listdir(PTA_file_path)
            database_files = [PTA_file_path + filename for filename in database_files]
            database_files = np.sort(database_files)
            hf_database_path = database_files[r]

            PTA_file_path = '/data/keeling/a/vllgsbr2/c/old_MAIA_Threshold_dev/LA_PTA_MODIS_Data/try2_database/observables_database/'
            database_files = os.listdir(PTA_file_path)
            database_files = [PTA_file_path + filename for filename in database_files]
            database_files = np.sort(database_files)
            hf_observables_path = database_files[r]

            PTA_file_path = '/data/keeling/a/vllgsbr2/c/old_MAIA_Threshold_dev/LA_PTA_MODIS_Data/try2_database/OLP_database/'
            database_files = os.listdir(PTA_file_path)
            database_files = [PTA_file_path + filename for filename in database_files]
            database_files = np.sort(database_files)
            hf_OLP_path    = database_files[r]

            observables = ['WI', 'NDVI', 'NDSI', 'visRef', 'nirRef', 'SVI', 'cirrus']
            print('Rank {} reporting for duty'.format(r))
            #get data for input into grouping function
            with h5py.File(hf_observables_path, 'r') as hf_observables,\
                 h5py.File(hf_database_path   , 'r') as hf_database,\
                 h5py.File(hf_OLP_path        , 'r') as hf_OLP:

                hf_database_keys = list(hf_database.keys())

                for time_stamp in hf_database_keys:
                    # lat = hf_database[time_stamp + '/geolocation/lat'][()]
                    # lon = hf_database[time_stamp + '/geolocation/lon'][()]
                    CM  = hf_database[time_stamp + '/cloud_mask/Unobstructed_FOV_Quality_Flag'][()]
                    OLP = hf_OLP[time_stamp + '/observable_level_paramter'][()]

                    obs_data = np.empty((1000,1000,7), dtype=np.float)
                    for i, obs in enumerate(observables):
                        data_path = '{}/{}'.format(time_stamp, obs)
                        #print(data_path, i, type(hf_observables[data_path][()][0,0]))#type(obs[:,:,i]))
                        obs_data[:,:,i] = hf_observables[data_path][()]
                    print('Rank {} has processed data'.format(r))
                    group_data(OLP, obs_data, CM, time_stamp)
                    print('Rank {} has grouped granule {}'.format(r, time_stamp))

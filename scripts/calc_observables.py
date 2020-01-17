import numpy as np
from svi_calculation import svi_calculation

def get_R(radiance, SZA, d, E_std_0b):
    """
    convert radiances to Bi-Directional Reflectance Factor, BRF, referred to as 'R'

    [Section 3.3.1.2]
    Convert spectral band radiances to BRF, based on the given solar zenith angle,
    earth sun distance, and the band weighted solar irradiance.

    Arguments:
        radiance {2D narray} -- contains MAIA radiance at any band
        SZA {2D narray} -- same shape as radiance; contains solar zenith angles in degrees
        d {float} -- earth sun distance in Astonomical Units(AU)
        E_std_0b {float} -- band weight solar irradiance at 1 AU,
                            corresponding to the radiance band

    Returns:
        2D narray -- BRF; same shape as radiance
    """
    #now filter out where cosSZA is too small with fill value
    invalid_cosSZA_idx = np.where(np.cos(np.deg2rad(SZA)) <= 0.01)
    radiance[invalid_cosSZA_idx] = -998

    #condition to not step on fill values when converting to BRF(R)
    valid_rad_idx = np.where(radiance >= 0.0)
    radiance[valid_rad_idx] = ((np.pi * radiance * d**2)\
                          / (np.cos(np.deg2rad(SZA)) * E_std_0b))[valid_rad_idx]
    #just assign R to the memory of radiance to highlight conversion
    R = radiance
    return R

#calculate sun-glint flag*******************************************************
#section 3.3.2.3
def get_sun_glint_mask(solarZenith, sensorZenith, solarAzimuth, sensorAzimuth,\
                       sun_glint_exclusion_angle, land_water_mask):
    """
    Calculate sun-glint flag.

    [Section 3.3.2.3]
    Sun-glint water pixels are set to 0;
    non-sun-glint water pixels and land pixels are set to 1.

    Arguments:
        solarZenith {2D narray} -- Solar zenith angle in degree
        sensorZenith {2D narray} -- MAIA zenith angle in degree
        solarAzimuth {2D narray} -- Solar azimuth angle in degree
        sensorAzimuth {2D narray} -- MAIA azimuth angle in degree
        sun_glint_exclusion_angle {float} -- maximum scattering angle (degree) for sun-glint
        land_water_mask {2D binary narray} -- specify the pixel is water (0) or land (1)

    Returns:
        2D binary narray -- sunglint mask over granule same shape as solarZenith
    """

    solarZenith               = np.deg2rad(solarZenith)
    sensorZenith              = np.deg2rad(sensorZenith)
    solarAzimuth              = np.deg2rad(solarAzimuth)
    sensorAzimuth             = np.deg2rad(sensorAzimuth)
    sun_glint_exclusion_angle = np.deg2rad(sun_glint_exclusion_angle)

    cos_theta_r = np.sin(sensorZenith) * np.sin(solarZenith) \
                * np.cos(sensorAzimuth - solarAzimuth - np.pi) + np.cos(sensorZenith) \
                * np.cos(solarZenith)
    theta_r = np.arccos(cos_theta_r)

    sun_glint_idx = np.where((theta_r >= 0) & \
                             (theta_r <= sun_glint_exclusion_angle))
    no_sun_glint_idx = np.where(~((theta_r >= 0) & \
                                  (theta_r <= sun_glint_exclusion_angle)))
    theta_r[sun_glint_idx]    = 0
    theta_r[no_sun_glint_idx] = 1
    #turn off glint calculated over land
    theta_r[land_water_mask == 1] = 1

    sun_glint_mask = theta_r

    return sun_glint_mask

#calculate observables**********************************************************
#section 3.3.2.1.2
#and band center wavelengths table 2 section 2.1
#R_NIR -> bands 9, 12, 13 -> 0.86, 1.61, 1.88 micrometers
#RGB channels -> bands 6, 5, 4, respectively

#whiteness index
def get_whiteness_index(R_band_6, R_band_5, R_band_4):
    """
    calculate whiteness index

    [Section 3.3.2.1.2]
    whiteness index (WI) uses 3 MAIA spectral bands (4, 5, 6).

    Arguments:
        R_band_6 {2D narray} -- BRF narray for band 6
        R_band_5 {2D narray} -- BRF narray for band 5
        R_band_4 {2D narray} -- BRF narray for band 4

    Returns:
        2D narray -- whiteness index same shape as input arrays
    """

    #data quality house keeping to retain fill values
    whiteness_index = np.ones(np.shape(R_band_6)) * -998
    whiteness_index[(R_band_6 == -999) | (R_band_5 == -999) | (R_band_4 == -999)] = -999
    valid_data_idx = np.where((R_band_6 >= 0) & (R_band_5 >= 0) & (R_band_4 >= 0))

    #calc WI
    visible_average = (R_band_6 + R_band_5 + R_band_4)/3
    whiteness_index[valid_data_idx] = \
            (np.abs(R_band_6 - visible_average)/visible_average + \
             np.abs(R_band_5 - visible_average)/visible_average + \
             np.abs(R_band_4 - visible_average)/visible_average)[valid_data_idx]

    return whiteness_index

#normalized difference vegetation index
def get_NDVI(R_band_6, R_band_9):
    """
    calculate normalized difference vegetation index (NDVI)

    [Section 3.3.2.1.2]
    NDVI uses 2 MAIA spectral bands (6 and 9).

    Arguments:
        R_band_6 {2D narray} -- BRF narray for band 6
        R_band_9 {2D narray} -- BRF narray for band 9

    Returns:
        2D narray -- NDVI same shape as any BRF input
    """

    #data quality house keeping to retain fill values
    NDVI = np.ones(np.shape(R_band_6)) * -998
    NDVI[(R_band_6 == -999) | (R_band_9 == -999)] = -999
    valid_data_idx = np.where((R_band_6 >= 0) & (R_band_9 >= 0))

    NDVI[valid_data_idx] = \
                         ((R_band_9 - R_band_6) / (R_band_9 + R_band_6))[valid_data_idx]

    return NDVI

#normalized difference snow index
def get_NDSI(R_band_5, R_band_12):
    """
    calculate normalized difference snow index (NDVI)

    [Section 3.3.2.1.2]
    NDVI uses 2 MAIA spectral bands (5 and 12).

    Arguments:
        R_band_5 {2D narray} -- BRF narray for band 5
        R_band_12 {2D narray} -- BRF narray for band 12

    Returns:
        2D narray -- NDSI same shape as any BRF input
    """
    #data quality house keeping to retain fill values
    NDSI = np.ones(np.shape(R_band_5)) * -998
    NDSI[(R_band_5 == -999) | (R_band_12 == -999)] = -999
    valid_data_idx = np.where((R_band_5 >= 0) & (R_band_12 >= 0))

    NDSI[valid_data_idx] = \
                         ((R_band_5 - R_band_12) / (R_band_5 + R_band_12))[valid_data_idx]

    return NDSI

#visible reflectance
def get_visible_reflectance(R_band_6):
    """
    return visible BRF of 0.64 um spectral band

    [Section 3.3.2.1.2]
    As the reflectance of band 6 has already been calculated, nothing more will be done.

    Arguments:
        R_band_6 {2D narray} -- BRF narray for band 6

    Returns:
        2D narray -- same as BRF input
    """
    return R_band_6

#near infra-red reflectance
def get_NIR_reflectance(R_band_9):
    """
    return NIR BRF of 0.86 um spectral band

    [Section 3.3.2.1.2]
    As the reflectance of band 9 has already been calculated, nothing more will be done.

    Arguments:
        R_band_9 {2D narray} -- BRF narray for band 9

    Returns:
        2D narray -- same as BRF input
    """
    return R_band_9

#spatial variability index
def get_spatial_variability_index(R_band_6):#, numrows, numcols):
    """
    calculate spatial variability index (SVI)

    [Section 3.3.2.1.2]
    SVI for a pixel is calculated as the standard deviation of aggregated 1-km R_0.64
    within a 3X3 matrix centered at the pixel.

    Arguments:
        R_band_6 {2D narray} -- BRF narray for band 6

    Returns:
        2D narray -- SVI array with the shape same as BRF input
    """


    #make copy to not modify original memory
    R_band_6_ = np.copy(R_band_6)
    R_band_6_[R_band_6_ == -998] = -999
    bad_value = -999
    min_valid_pixels = 9
    spatial_variability_index = \
                            svi_calculation(R_band_6_, bad_value, min_valid_pixels)

    #data quality house keeping
    spatial_variability_index[R_band_6 == -998] = -998
    spatial_variability_index[R_band_6 == -999] = -999

    return spatial_variability_index

#cirrus test
def get_cirrus_Ref(R_band_13):
    """
    return NIR BRF of 1.88 um spectral band

    [Section 3.3.2.1.2]
    As the reflectance of band 13 has already been calculated, nothing more will be done.

    Arguments:
        R_band_13 {2D narray} -- BRF narray for band 13

    Returns:
        2D narray -- same as BRF input
    """
    return R_band_13

if __name__ == '__main__':

    import h5py
    import mpi4py.MPI as MPI
    import tables
    import os
    import numpy as np
    tables.file._open_files.close_all()

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()

    # if rank==0:
    #
    #     #open database to read
    #     PTA_file_path    = '/data/keeling/a/vllgsbr2/c/old_MAIA_Threshold_dev/LA_PTA_MODIS_Data/try2_database/'
    #     database_files   = os.listdir(PTA_file_path)
    #     database_files   = [PTA_file_path + filename for filename in database_files]
    #     database_files   = np.sort(database_files)
    #
    #     #record howmany time stamps in each database
    #     #and calculate howmany processors can be used for each database
    #     cpus_per_file           = (size-2) // len(database_files)
    #     num_timestamps_per_file = np.array([len(list(h5py.File(f, 'r+').keys())) for f in database_files])
    #     timestamps_per_cpu      = num_timestamps_per_file // (size-2)
    #
    #     data = timestamps_per_cpu, num_timestamps_per_file, cpus_per_file
    #     for i in range(1,size):
    #         comm.send(data=data, dest=i)

    for r in range(size):

        if rank==r:

            #open database to read
            PTA_file_path = '/data/keeling/a/vllgsbr2/c/old_MAIA_Threshold_dev/LA_PTA_MODIS_Data/try2_database/'
            database_files = os.listdir(PTA_file_path)
            database_files = [PTA_file_path + filename for filename in database_files]
            database_files = np.sort(database_files)
            hf_database_path = database_files[r]
            with h5py.File(hf_database_path, 'r+') as hf_database:

                hf_database_keys = list(hf_database.keys())

                observables = ['WI', 'NDVI', 'NDSI', 'visRef', 'nirRef', 'SVI', 'cirrus']

                #create/open hdf5 file to store observables
                PTA_file_path   = '/data/keeling/a/vllgsbr2/c/old_MAIA_Threshold_dev/LA_PTA_MODIS_Data'
                hf_observables_path = '{}/LA_PTA_observables_start_{}_end_{}_.hdf5'.format(PTA_file_path, start, end)

                # try:
                with h5py.File(hf_observables_path, 'w') as hf_observables:
                    for time_stamp in hf_database_keys:

                        R_band_4  = hf_database[time_stamp + '/reflectance/band_3'][()]
                        R_band_5  = hf_database[time_stamp + '/reflectance/band_4'][()]
                        R_band_6  = hf_database[time_stamp + '/reflectance/band_1'][()]
                        R_band_9  = hf_database[time_stamp + '/reflectance/band_2'][()]
                        R_band_12 = hf_database[time_stamp + '/reflectance/band_6'][()]
                        R_band_13 = hf_database[time_stamp + '/reflectance/band_26'][()]

                        sun_glint_mask            = hf_database[time_stamp + '/cloud_mask/Sun_glint_Flag'][()]

                        whiteness_index           = get_whiteness_index(R_band_6, R_band_5, R_band_4)
                        NDVI                      = get_NDVI(R_band_6, R_band_9)
                        NDSI                      = get_NDSI(R_band_5, R_band_12)
                        visible_reflectance       = get_visible_reflectance(R_band_6)
                        NIR_reflectance           = get_NIR_reflectance(R_band_9)
                        spatial_variability_index = get_spatial_variability_index(R_band_6)#, numrows, numcol)
                        cirrus_Ref                = get_cirrus_Ref(R_band_13)

                        data = np.dstack((whiteness_index, NDVI, NDSI,\
                                          visible_reflectance, NIR_reflectance,\
                                          spatial_variability_index, cirrus_Ref))

                        for i in range(7):
                            try:
                                group = hf_observables.create_group(time_stamp)
                                group.create_dataset(observables[i], data=data[:,:,i], compression='gzip')
                            except:
                                try:
                                    group.create_dataset(observables[i], data=data[:,:,i], compression='gzip')
                                except:
                                    hf_observables[time_stamp+'/'+observables[i]][:] = data[:,:,i]
                # except:
                #     with h5py.File(hf_observables_path, 'r+') as hf_observables:
                #
                #         for time_stamp in hf_database_keys:
                #
                #             R_band_4  = hf_database[time_stamp + '/reflectance/band_3'][()]
                #             R_band_5  = hf_database[time_stamp + '/reflectance/band_4'][()]
                #             R_band_6  = hf_database[time_stamp + '/reflectance/band_1'][()]
                #             R_band_9  = hf_database[time_stamp + '/reflectance/band_2'][()]
                #             R_band_12 = hf_database[time_stamp + '/reflectance/band_6'][()]
                #             R_band_13 = hf_database[time_stamp + '/reflectance/band_26'][()]
                #
                #             sun_glint_mask            = hf_database[time_stamp + '/cloud_mask/Sun_glint_Flag'][()]
                #
                #             whiteness_index           = get_whiteness_index(R_band_6, R_band_5, R_band_4)
                #             NDVI                      = get_NDVI(R_band_6, R_band_9)
                #             NDSI                      = get_NDSI(R_band_5, R_band_12)
                #             visible_reflectance       = get_visible_reflectance(R_band_6)
                #             NIR_reflectance           = get_NIR_reflectance(R_band_9)
                #             spatial_variability_index = get_spatial_variability_index(R_band_6)#, numrows, numcol)
                #             cirrus_Ref                = get_cirrus_Ref(R_band_13)
                #
                #             data = np.dstack((whiteness_index, NDVI, NDSI,\
                #                               visible_reflectance, NIR_reflectance,\
                #                               spatial_variability_index, cirrus_Ref))
                #
                #             for i in range(7):
                #                 try:
                #                     group = hf_observables.create_group(time_stamp)
                #                     group.create_dataset(observables[i], data=data[:,:,i], compression='gzip')
                #                 except:
                #                     try:
                #                         group.create_dataset(observables[i], data=data[:,:,i], compression='gzip')
                #                         hf_observables[time_stamp+'/'+observables[i]][:] = data[:,:,i]
                #                     except:
                #                         hf_observables[time_stamp+'/'+observables[i]][:] = data[:,:,i]
































                #

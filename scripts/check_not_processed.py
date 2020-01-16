import pandas as pd
import os

#get txt files
home = '/data/keeling/a/vllgsbr2/c/MAIA_thresh_dev/MAIA_CloudMask_Threshold_Development/scripts/MPI_create_dataset_output'
files = os.listdir(home)

#master dataframe to store all time stamps processed
master_df = pd.DataFrame()
master_df.columns = ['time_stamps']

for file in files:
    temp_df = pd.read_csv(file)
    temp_df.columns = ['num', 'time_stamp', 'phrase']

    master_df.append(temp_df['time_stamp'])

processed_files = list(master_df['time_stamps'])

home = '/data/keeling/a/vllgsbr2/c/old_MAIA_Threshold_dev/'
files = 'LAADS_query.2019-10-15T18_07.csv'

laads_query_df = pd.read_csv(home+file)
file_name_column = 'fileUrls from query MOD021KM--61 MOD03--61 MOD35_L2'\
                   '--61 2002-01-01..2019-10-15 x-124.4y39.8 x-112.8y30.7[5]'
all_files = list(laads_query_df[file_name_column])

# check_df = pd.DataFrame()
# check_df.columns = ['time_stamps', 'processed_1_not_processed_0']

check = open('./check_processed.csv')
check.write('time_stamps,processed_1_not_processed_0\n')

#choose PTA from keeling
PTA_file_path   = '/data/keeling/a/vllgsbr2/c/old_MAIA_Threshold_dev/LA_PTA_MODIS_Data'

#grab files names for PTA
filename_MOD_02 = np.array(os.listdir(PTA_file_path + '/MOD_02'))
filename_MOD_03 = np.array(os.listdir(PTA_file_path + '/MOD_03'))
filename_MOD_35 = np.array(os.listdir(PTA_file_path + '/MOD_35'))

#sort files by time so we can access corresponding files without
#searching in for loop
filename_MOD_02 = np.sort(filename_MOD_02)
filename_MOD_03 = np.sort(filename_MOD_03)
filename_MOD_35 = np.sort(filename_MOD_35)

#grab time stamp (YYYYDDD.HHMM) to name each group after the granule
#it comes from
time_stamps_downloaded = [x[10:22] for x in filename_MOD_02]
# filename_MOD_03_timeStamp = [x[7:19]  for x in filename_MOD_03]
# filename_MOD_35_timeStamp = [x[10:22] for x in filename_MOD_35]

for i in time_stamps_downloaded:
    found = False
    for j in processed_files:
        if i==j:
            check.write('{},{}\n'.format(i, 1)
            found = True
    if not found:
        check.write('{},{}\n'.format(i, 0))
        found = False

check.close()

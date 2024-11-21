# open_ran_datacenter_placement
Open RAN Datacente Placement


# Instructions

1) Create the filtered dataset:

Make sure you have the database from Anatel Website in the same folder as the pre-process script. In this repository, we have placed the datebases from both Natal and Manaus, cities from Brazil. For now, you should choose which dataset you want to create in the python script (located in CityData/), according with the command: 

```
$ python3 preprocess_anatel_city_csv.py <dataset> <output_filename_dataset>

```

After creating the dataset, you shoud follow the instructions below. 

2) How to Reproduce Our Results:

2.1) Open the Create_Campaigns.ipynb notebook and follow the instructions provided. If everything is set up correctly, you should see two directories created within the Campaigns/ folder: one for Natal and the other for Manaus.

2.2) Navigate to one of the directories and run the following commands:

```
$ chmod +x Placement_<city>_Case_1_2_local_odcs_AllJOBS0.sh
$ ./Placement_<city>_Case_1_2_local_odcs_AllJOBS0.sh

```
Currently, there are five shell scripts, each of which will execute 20 jobs. In total, 100 jobs will be run. If you'd like to adjust the number of jobs, return to Create_Campaigns.ipynb and modify the jobs and numberOfJobsShellScript parameters.




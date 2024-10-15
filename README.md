# open_ran_datacenter_placement
Open RAN Datacente Placement


# Instructions

1) Create the filtered dataset:

Make sure you have the database from Anatel Website in the same folder as the pre-process script. In this repository, we have placed the datebases from both Natal and Manaus, cities from Brazil. For now, you should choose which dataset you want to create in the python script (located in CityData/), according with the command: 

```
$ python3 preprocess_anatel_city_csv.py <dataset> <output_filename_dataset>

```

After creating the dataset, you shoud run campaign.sh as the example below. Do not forget to the add the created dataset as argument as well.

2) How to run the campaign.sh:
```
$ chmod +x campaign.sh

$ ./campaign.sh -j 5 -c 14 -d 11 -C 1000 -o 1 -n "CampaignName" -w 0.4,0.4,0.2 <output_filename_dataset>

```

Code will run 5 times, where each run means a different random seed is used.

# open_ran_datacenter_placement
Open RAN Datacente Placement


# Instructions

1) Create the dataset (Natal or Manaus):

Make sure you have the database from AnatelWebsite in the same folder as the pre-process script. In this repository, we have placed the datebases from both Natal and Manaus, cities from Brazil. For now, you should choose which dataset you want to create by changing the variable "filename" in the python script (located in CityData/). It will create a filtered dataset with the same name you placed in "filename".

```
$ python3 preprocess_anatel_city_csv.py

```

After creating, make sure odc_placement_parser.py reads the created dataset.

2) How to run the campaign.sh:
```
$ chmod +x campaign.sh

$ ./campaign.sh -j 5 -c 14 -d 11 -C 1000 -o 1 -n "CampaignName" -w 0.4,0.4,0.2

```

Code will run 5 times, where each run means a different random seed is used.

# Campaign Generation

## Instructions  
The first step is to open the file **Create_Campaigns.ipynb** using Jupyter Notebook. Campaign generation consists of four steps, described below:  

1. Insert the folder where the script is located;  
   * In this repository, it refers to the **Campaigns** folder:  
   ```
   "/home/.../open_ran_datacenter_placement/Campaigns/"
   ```  
2. Create the random seeds file;  
   * This step needs to be performed only once.  
3. Generate the campaign generation script;  
   * The **Create_Campaigns.py** file is generated, which is the script responsible for campaign generation.  

The next two steps are exemplified for each city addressed in the study.  

4. Configure the folders used in the campaign;  
   * It is recommended to use names that reflect the purpose of the campaign being generated.  
5. Configure and generate the **.yaml** file;  
   * It is recommended that the **.yaml** file has the same name as the chosen campaign folder.  

   The **.yaml** file contains all campaign settings, as shown below:  

   1. Campaign generation script configurations;  
   ```
   ScriptParameters:
     script: odc_placement_parser.py # Script name
     local_path: /home/.../Repositories/open_ran_datacenter_placement/ # Path where your script is located
     cluster_path: /home/rqdfhsilva/CPQD/ # Path where your script is located
     environment_name: cpqd # Name of the virtual environment created in the cluster
     outputDir:
       - outputDir # Parameter name in your script
       - /home/oai-ufrn/Repositories/open_ran_datacenter_placement/Results/ # Path where your results will be placed (your script must have this parameter)
     seed: seed # Parameter name of the random seed used in your script      
     CampaignTag: Case1_2 # Output filename
     simLocation: intel-256 # Set the location of the simulation (local or cluster system name)
   ```  
   2. Campaign organization settings;  
   ```
   ShellScriptParameters:    
     nOfCurlines: 3      # Number of campaign lines
     SimTied: 1
     nOfCurlinesTied: 3  # If greater than nOfCurlines, it means campaignX is included 
     daytime: 0          # Number of days to simulate (only for cluster simulation)  
     htime: 1            # Number of hours to simulate (only for cluster simulation) 
     ntasks: 8           # Number of simulations in one job (IMPORTANT)
     cpusPerTask: 16     # Number of CPUs per task
     numberOfJobsShellScript: 10
    ```  
      * **nOfCurlines**: Specifies the number of campaign lines in the simulation. This value cannot be greater than the number of variables provided in the **campaignLines** parameter of the next configuration set.  
      * **SimTied**: Indicates if there is a tied variable in the simulation, i.e., one that changes only if another variable changes.  
      * **nOfCurlinesTied**: Specifies the number of tied variables. This cannot be greater than **nOfCurlines**. If it is smaller, only the first tied variables equal to the specified value are considered.  
        * Example: **nOfCurlines=3**, **SimTied=1**, **nOfCurlinesTied=2**. This means that only 2 of the 3 variables are tied; the two tied variables are the first two from **campaignLines**.  
        * Configurations implemented (**nOfCurlines/SimTied/nOfCurlinesTied**):  
          * 1/0/0  
          * 2/0/0  
          * 3/0/0  
          * 4/0/0  
          * 2/1/2  
          * 3/1/2  
          * 3/1/3  
          * 4/1/2  
          * 5/1/2   
   3. Parameters used in the campaign;  
      * These are the parameters that vary in the campaign. Specify which parameter(s) will make up the curve(s) in the graph and which one (ONLY 1) will be on the X-axis of the graphs.  
      ```
      campaignLines:
        campaignX: # campaignX: parameter name to vary on the X-axis (ONLY 1)
          - odcs
        campaignLines: # campaignLines: parameter name to vary in different lines
          - wcpu
          - wodc
          - wd
        jobs: 100 # Number of jobs to run 
      ```  
   4. Parameters used in the simulation.  
      ```
      scenarioParameters: 
        cpuper100:
          - 14
        maxdistance: # Simulation duration (seconds)
          - 11
        capacity:
          - 1000
        odcs:
          - 0
          - 493
          - 328
          - 246
        trials: 
          - 60
        population: 
          - 300
        process:
          - 8
        wcpu:
          - 0
          - 0.5
        wodc:
          - 0
          - 0
        wd:
          - 1
          - 0.5
        csv: # Path of the CSV file used in the simulation
          - /home/rqdfhsilva/CPQD/CityData/SaoPaulo.csv 
      ```
6. Run the Creation_Campaigns.py script.
   ```
   %run Create_Campaigns -f "Placement_SaoPaulo_Case_1_2_cluster.yaml"
   ```

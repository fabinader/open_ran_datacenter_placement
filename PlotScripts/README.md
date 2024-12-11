# Plot Scripts

## Instructions
### Convergence Plots:  
   * The **ConvergencePlot.ipynb** file is used to generate plots for visualizing the convergence of the metrics `fiberlength` and `capacity` for each simulation generated during the campaign. The step-by-step usage is described below:  
   1. Specify the location of the **ConvergencePlot.ipynb** file;  
   2. Generate the script file **ConvergencePlot.py**;  
      * The **ConvergencePlot.py** script implements the logic for data retrieval, considering the number of JOBs and the metrics (`fiberlength` and `capacity`).  
   3. Run the **ConvergencePlot.py** script with the appropriate configurations:  
      * `-j`: Number of JOBs to be plotted;  
      * `-f`: Configuration file name;  
      * `-p`: Path to the campaign results;  
      * `-s`: Path where the convergence plots will be saved.  
      ```bash
      %run ConvergencePlot -j "20" -f "Placement_SaoPaulo_Case_1_2_cluster.yaml" -p '/home/oai-ufrn/Repositories/open_ran_datacenter_placement/Results/results_Placement_SaoPaulo_Case_1_2_cluster_odcs/' -s '/home/oai-ufrn/Repositories/open_ran_datacenter_placement/PlotResults/'
      ```

### Results Plots:  
   * TBA (To Be Announced)



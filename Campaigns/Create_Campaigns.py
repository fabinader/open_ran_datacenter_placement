import os
import argparse
import pickle
import numpy as np

# To install YAML: sudo apt-get install python3-yaml
import yaml

class Simulation:
    def __init__(self, configurations_file):
        #self.email_to = 'sicrano@gmail.com'            
        with open(configurations_file, 'r') as f:
            self.doc = yaml.load(f, Loader=yaml.loader.BaseLoader)
        self.campaign_name = os.path.splitext(configurations_file)[0]
       
        # Simu parameters
        self.commandScript = ''
        for iscenarioParameters in self.doc['scenarioParameters'].items():
            commandraw= " --"+str(iscenarioParameters[0])+"="+str(iscenarioParameters[1][0])
            self.commandScript = self.commandScript + commandraw
        #print (self.commandScript)
    
        # ns-3 script configuration
        self.script = str(self.doc['ScriptParameters']['script'])
        self.local_path = str(self.doc['ScriptParameters']['local_path'])
        #self.local_path = os.getcwd() + '/' + self.local_path
        self.cluster_path = str(self.doc['ScriptParameters']['cluster_path'])
        self.outputDirName = str(self.doc['ScriptParameters']['outputDir'][0])
        self.outputDir = str(self.doc['ScriptParameters']['outputDir'][1])
        self.seed = str(self.doc['ScriptParameters']['seed'])
        self.CampaignTag = str(self.doc['ScriptParameters']['CampaignTag'])
        self.configurations_file = configurations_file       
        self.simLocation = str(self.doc['ScriptParameters']['simLocation'])
        
        # Shell Script Parameters configuration
        self.nOfCurlines=self.doc['ShellScriptParameters']['nOfCurlines']
        self.SimTied = self.doc['ShellScriptParameters']['SimTied']
        self.nOfCurlinesTied = self.doc['ShellScriptParameters']['nOfCurlinesTied']
        self.daytime  = self.doc['ShellScriptParameters']['daytime']
        self.htime  = self.doc['ShellScriptParameters']['htime']
        self.ntasks = self.doc['ShellScriptParameters']['ntasks']
        self.cpusPerTask = self.doc['ShellScriptParameters']['cpusPerTask']
        self.numberOfJobsShellScript = int(self.doc['ShellScriptParameters']['numberOfJobsShellScript'])
        
         #Lines/curves
        self.campaignX = self.doc['campaignLines']['campaignX']
        self.campaignLines = self.doc['campaignLines']['campaignLines']
        self.nJobs = int(self.doc['campaignLines']['jobs'])
        
    def recursiveCommand(self,CurLine,scenarioParameters,vposition):
        command = (" --"+CurLine+"="+scenarioParameters[CurLine][vposition])
        return command
        
    
    def runCampaign(self,curCampaign):
        # Configure simulation file in accordance with campaign parameter
        numberOfJobsShellScript = self.numberOfJobsShellScript
        for iCallScripts in range (0,int(self.nJobs/numberOfJobsShellScript)):
            sh_name_main = self.campaign_name + '_' + self.simLocation + '_' + curCampaign + '_AllJOBS'+str(iCallScripts) +".sh"
            print("Main Shell Script: " + sh_name_main)  
            with open(sh_name_main, "w") as f:
                f.write("#!/bin/bash\n")
                #f.write("cd "+ self.cluster_path +"\n")
                for iJob in range(iCallScripts*numberOfJobsShellScript,iCallScripts*numberOfJobsShellScript + numberOfJobsShellScript):
                    for iSim in range(0, int(self.ntasks)):
                        sh_name = "run_"+self.campaign_name + '_' + self.simLocation + '_' + curCampaign + '_JOB' + str(iJob) + '_Sim_' + str(iSim)
                        if self.simLocation == 'cluster' or self.simLocation == 'service' or self.simLocation == 'intel-512' or self.simLocation == 'intel-256':
                            f.write("sbatch -p " + self.simLocation + " " + sh_name + ".sh" + "\n")
                        else:
                            f.write("chmod +x " + sh_name + ".sh" + " & wait\n")
                            f.write("./" + sh_name + ".sh" + " & wait\n")          
        for iJob in range(0,self.nJobs):         
            nOfCurlines=int(self.nOfCurlines[0]) # number of Campaign Lines in 1 simulation (max value = 3)
            SimTied = int(self.SimTied[0]) # whether or not the simulation parameters are tied (0 or 1)
            nOfCurlinesTied = int(self.nOfCurlinesTied[0]) # number of Campaign Lines tied (max value = nOfCurlines)
            with open('ListOfRandomNumbers.pkl', 'rb') as f:
                    jobRunSeed = pickle.load(f)
            count = 0
            if nOfCurlines == 1 and SimTied == 0:
                curline = self.campaignLines[0]
                count=0
                with open('ListOfRandomNumbers.pkl', 'rb') as f:
                    jobRunSeed = pickle.load(f)
                for i in range(len(self.doc['scenarioParameters'][curline])):    
                    for varParam in self.doc['scenarioParameters'][curCampaign]:
                        sh_name = self.campaign_name + '_' + self.simLocation + '_' + curCampaign + '_JOB' + str(iJob) + '_Sim_' + str(count)
                        print(curCampaign+" campaign written in file: " 'run_%s.sh' % sh_name)
                        with open('run_%s.sh' % sh_name, 'w') as f:                    
                            f.write('#!/bin/bash\n')
                            if self.simLocation == 'cluster' or self.simLocation == 'service' or self.simLocation == 'intel-512' or self.simLocation == 'intel-256':
                                print("TODO")
                            else:
                                outputDir = self.outputDir + 'results_' + self.campaign_name + '_' + curCampaign
                                f.write('mkdir -p '+outputDir+"/JOB"+str(iJob)+"/Sim_"+str(count) +'\n')
                                f.write('cp -f run_'+sh_name+'.sh'+' '+outputDir+'\n')
                                f.write('cp -f '+self.configurations_file+ ' ' +outputDir+'\n')
                                f.write("cd '"+self.local_path+"'"+"\n")
                                f.write("sleep $((11 + RANDOM % 50))"+"\n")
                                command1 = (
                                "python3 " + self.script +
                                " --"+self.outputDirName+"="+outputDir +
                                " --"+self.seed+"="+str(jobRunSeed[iJob]))
                            command3 =(
                            " --"+curline+"="+self.doc['scenarioParameters'][curline][i]+
                            " --"+curCampaign+"="+varParam+
                            "' > "+outputDir+"/JOB"+str(iJob)+'/Sim_' + str(count)+'.out 2>&1')
                            f.write(command1+self.commandScript+command3+'\n')
                            count = count + 1
                                
            elif nOfCurlines==2 and SimTied == 0:
                with open('ListOfRandomNumbers.pkl', 'rb') as f:
                    jobRunSeed = pickle.load(f)
                curline = self.campaignLines[0]
                curline1 = self.campaignLines[1]
                count=0
                for i in range(len(self.doc['scenarioParameters'][curline])):
                    for j in range(len(self.doc['scenarioParameters'][curline1])):
                        for varParam in self.doc['scenarioParameters'][curCampaign]:
                            sh_name = self.campaign_name + '_' + self.simLocation + '_' + curCampaign + '_JOB' + str(iJob) + '_Sim_' + str(count)
                            print(curCampaign+" campaign written in file: " 'run_%s.sh' % sh_name)
                            with open('run_%s.sh' % sh_name, 'w') as f:                    
                                f.write('#!/bin/bash\n')
                                if self.simLocation == 'cluster' or self.simLocation == 'service' or self.simLocation == 'intel-512' or self.simLocation == 'intel-256':
                                    print("TODO")
                                else:
                                    outputDir = self.outputDir + 'results_' + self.campaign_name + '_' + curCampaign
                                    f.write('mkdir -p '+outputDir+"/JOB"+str(iJob)+"/Sim_"+str(count) +'\n')
                                    f.write('cp -f run_'+sh_name+'.sh'+' '+outputDir+'\n')
                                    f.write('cp -f '+self.configurations_file+ ' ' +outputDir+'\n')
                                    f.write("cd '"+self.local_path+"'"+"\n")
                                    f.write("sleep $((11 + RANDOM % 50))"+"\n")
                                    command1 = (
                                    "python3 " + self.script +
                                    " --"+self.outputDirName+"="+outputDir +
                                    " --"+self.seed+"="+str(jobRunSeed[iJob]))
                                command3 =(
                                " --"+curline+"="+self.doc['scenarioParameters'][curline][i]+
                                " --"+curline1+"="+self.doc['scenarioParameters'][curline1][j]+
                                " --"+curCampaign+"="+varParam+
                                "' > "+outputDir+"/JOB"+str(iJob)+'/Sim_' + str(count)+'.out 2>&1')
                                f.write(command1+self.commandScript+command3+'\n')
                                count = count + 1
                            

            elif nOfCurlines == 3 and SimTied == 0:
                with open('ListOfRandomNumbers.pkl', 'rb') as f:
                    jobRunSeed = pickle.load(f)
                curline = self.campaignLines[0]
                curline1 = self.campaignLines[1]
                curline2 = self.campaignLines[2]
                count=0;
                for i in range(len(self.doc['scenarioParameters'][curline])):
                    for j in range(len(self.doc['scenarioParameters'][curline1])):
                        for k in range(len(self.doc['scenarioParameters'][curline2])):
                            for varParam in self.doc['scenarioParameters'][curCampaign]:
                                sh_name = self.campaign_name + '_' + self.simLocation + '_' + curCampaign + '_JOB' + str(iJob) + '_Sim_' + str(count)
                                print(curCampaign+" campaign written in file: " 'run_%s.sh' % sh_name)
                                with open('run_%s.sh' % sh_name, 'w') as f:                    
                                    f.write('#!/bin/bash\n')
                                    if self.simLocation == 'cluster' or self.simLocation == 'service' or self.simLocation == 'intel-512' or self.simLocation == 'intel-256':
                                        print("TODO")
                                    else:
                                        outputDir = self.outputDir + 'results_' + self.campaign_name + '_' + curCampaign
                                        f.write('mkdir -p '+outputDir+"/JOB"+str(iJob)+"/Sim_"+str(count) +'\n')
                                        f.write('cp -f run_'+sh_name+'.sh'+' '+outputDir+'\n')
                                        f.write('cp -f '+self.configurations_file+ ' ' +outputDir+'\n')
                                        f.write("cd '"+self.local_path+"'"+"\n")
                                        f.write("sleep $((11 + RANDOM % 50))"+"\n")
                                        command1 = (
                                        "python3 " + self.script +
                                        " --"+self.outputDirName+"="+outputDir +
                                        " --"+self.seed+"="+str(jobRunSeed[iJob]))
                                    command3 =(
                                    " --"+curline+"="+self.doc['scenarioParameters'][curline][i]+
                                    " --"+curline1+"="+self.doc['scenarioParameters'][curline1][j]+
                                    " --"+curline2+"="+self.doc['scenarioParameters'][curline2][k]+
                                    " --"+curCampaign+"="+varParam+
                                    "' > "+outputDir+"/JOB"+str(iJob)+'/Sim_' + str(count)+'.out 2>&1')
                                    f.write(command1+self.commandScript+command3+'\n')
                                    count = count + 1
            
            elif nOfCurlines == 4 and SimTied == 0:
                with open('ListOfRandomNumbers.pkl', 'rb') as f:
                    jobRunSeed = pickle.load(f)
                curline = self.campaignLines[0]
                curline1 = self.campaignLines[1]
                curline2 = self.campaignLines[2]
                curline3 = self.campaignLines[3]
                count=0;
                for i in range(len(self.doc['scenarioParameters'][curline])):
                    for j in range(len(self.doc['scenarioParameters'][curline1])):
                        for k in range(len(self.doc['scenarioParameters'][curline2])):
                            for n in range(len(self.doc['scenarioParameters'][curline3])):
                                for varParam in self.doc['scenarioParameters'][curCampaign]:
                                    sh_name = self.campaign_name + '_' + self.simLocation + '_' + curCampaign + '_JOB' + str(iJob) + '_Sim_' + str(count)
                                    print(curCampaign+" campaign written in file: " 'run_%s.sh' % sh_name)
                                    with open('run_%s.sh' % sh_name, 'w') as f:                    
                                        f.write('#!/bin/bash\n')
                                        if self.simLocation == 'cluster' or self.simLocation == 'service' or self.simLocation == 'intel-512' or self.simLocation == 'intel-256':
                                            print("TODO")
                                        else:
                                            outputDir = self.outputDir + 'results_' + self.campaign_name + '_' + curCampaign
                                            f.write('mkdir -p '+outputDir+"/JOB"+str(iJob)+"/Sim_"+str(count) +'\n')
                                            f.write('cp -f run_'+sh_name+'.sh'+' '+outputDir+'\n')
                                            f.write('cp -f '+self.configurations_file+ ' ' +outputDir+'\n')
                                            f.write("cd '"+self.local_path+"'"+"\n")
                                            f.write("sleep $((11 + RANDOM % 50))"+"\n")
                                            command1 = (
                                            "python3 " + self.script +
                                            " --"+self.outputDirName+"="+outputDir +
                                            " --"+self.seed+"="+str(jobRunSeed[iJob]))
                                        command3 =(
                                        " --"+curline+"="+self.doc['scenarioParameters'][curline][i]+
                                        " --"+curline1+"="+self.doc['scenarioParameters'][curline1][j]+
                                        " --"+curline2+"="+self.doc['scenarioParameters'][curline2][k]+
                                        " --"+curline3+"="+self.doc['scenarioParameters'][curline3][n]+
                                        " --"+curCampaign+"="+varParam+
                                        "' > "+outputDir+"/JOB"+str(iJob)+'/Sim_' + str(count)+'.out 2>&1')
                                        f.write(command1+self.commandScript+command3+'\n')
                                        count = count + 1
        
            elif nOfCurlines == 2 and SimTied == 1 and nOfCurlinesTied == 2:
                with open('ListOfRandomNumbers.pkl', 'rb') as f:
                    jobRunSeed = pickle.load(f)
                curline = self.campaignLines[0]
                curline1 = self.campaignLines[1]
                #curline=self.doc['scenarioParameters'][campaignLines][0]
                #curline1=self.doc['scenarioParameters'][campaignLines][1]
                count=0
                for i in range(len(self.doc['scenarioParameters'][curline])):
                    for varParam in self.doc['scenarioParameters'][curCampaign]:
                        sh_name = self.campaign_name + '_' + self.simLocation + '_' + curCampaign + '_JOB' + str(iJob) + '_Sim_' + str(count)
                        print(curCampaign+" campaign written in file: " 'run_%s.sh' % sh_name)
                        with open('run_%s.sh' % sh_name, 'w') as f:
                            f.write('#!/bin/bash\n')
                            if self.simLocation == 'cluster' or self.simLocation == 'service' or self.simLocation == 'intel-512' or self.simLocation == 'intel-256':
                                print("TODO")
                            else:
                                outputDir = self.outputDir + 'results_' + self.campaign_name + '_' + curCampaign
                                f.write('mkdir -p '+outputDir+"/JOB"+str(iJob)+"/Sim_"+str(count) +'\n')
                                f.write('cp -f run_'+sh_name+'.sh'+' '+outputDir+'\n')
                                f.write('cp -f '+self.configurations_file+ ' ' +outputDir+'\n')
                                f.write("cd '"+self.local_path+"'"+"\n")
                                f.write("sleep $((11 + RANDOM % 50))"+"\n")
                                command1 = (
                                "python3 " + self.script +
                                " --"+self.outputDirName+"="+outputDir +
                                " --"+self.seed+"="+str(jobRunSeed[iJob]))
                            command3 =(
                            " --"+curline+"="+self.doc['scenarioParameters'][curline][i]+
                            " --"+curline1+"="+self.doc['scenarioParameters'][curline1][i]+
                            " --"+curCampaign+"="+varParam+
                            "' > "+outputDir+"/JOB"+str(iJob)+'/Sim_' + str(count)+'.out 2>&1')
                            f.write(command1+self.commandScript+command3+'\n')
                            count = count + 1

                        
            elif nOfCurlines == 3 and SimTied == 1 and nOfCurlinesTied == 2:
                with open('ListOfRandomNumbers.pkl', 'rb') as f:
                    jobRunSeed = pickle.load(f)
                curline = self.campaignLines[0]
                curline1 = self.campaignLines[1]
                curline2 = self.campaignLines[2]
                count=0;
                for i in range(len(self.doc['scenarioParameters'][curline])):
                    for k in range(len(self.doc['scenarioParameters'][curline2])):
                        for varParam in self.doc['scenarioParameters'][curCampaign]:
                            sh_name = self.campaign_name + '_' + self.simLocation + '_' + curCampaign + '_JOB' + str(iJob) + '_Sim_' + str(count)
                            print(curCampaign+" campaign written in file: " 'run_%s.sh' % sh_name)
                            with open('run_%s.sh' % sh_name, 'w') as f:
                                f.write('#!/bin/bash\n')
                                if self.simLocation == 'cluster' or self.simLocation == 'service' or self.simLocation == 'intel-512' or self.simLocation == 'intel-256':
                                    print("TODO")
                                else:
                                    outputDir = self.outputDir + 'results_' + self.campaign_name + '_' + curCampaign
                                    f.write('mkdir -p '+outputDir+"/JOB"+str(iJob)+"/Sim_"+str(count) +'\n')
                                    f.write('cp -f run_'+sh_name+'.sh'+' '+outputDir+'\n')
                                    f.write('cp -f '+self.configurations_file+ ' ' +outputDir+'\n')
                                    f.write("cd '"+self.local_path+"'"+"\n")
                                    f.write("sleep $((11 + RANDOM % 50))"+"\n")
                                    command1 = (
                                    "python3 " + self.script +
                                    " --"+self.outputDirName+"="+outputDir +
                                    " --"+self.seed+"="+str(jobRunSeed[iJob]))
                                command3 =(
                                " --"+curline+"="+self.doc['scenarioParameters'][curline][i]+
                                " --"+curline1+"="+self.doc['scenarioParameters'][curline1][i]+
                                " --"+curline2+"="+self.doc['scenarioParameters'][curline2][k]+
                                " --"+curCampaign+"="+varParam+
                                "' > "+outputDir+"/JOB"+str(iJob)+'/Sim_' + str(count)+'.out 2>&1')
                                f.write(command1+self.commandScript+command3+'\n')
                                count = count + 1
            
            elif nOfCurlines == 3 and SimTied == 1 and nOfCurlinesTied == 3:
                with open('ListOfRandomNumbers.pkl', 'rb') as f:
                    jobRunSeed = pickle.load(f)
                curline = self.campaignLines[0]
                curline1 = self.campaignLines[1]
                curline2 = self.campaignLines[2]
                count=0
                for i in range(len(self.doc['scenarioParameters'][curline])):
                    for varParam in self.doc['scenarioParameters'][curCampaign]:
                        sh_name = self.campaign_name + '_' + self.simLocation + '_' + curCampaign + '_JOB' + str(iJob) + '_Sim_' + str(count)
                        print(curCampaign+" campaign written in file: " 'run_%s.sh' % sh_name)
                        with open('run_%s.sh' % sh_name, 'w') as f:
                            f.write('#!/bin/bash\n')
                            if self.simLocation == 'cluster' or self.simLocation == 'service' or self.simLocation == 'intel-512' or self.simLocation == 'intel-256':
                                print("TODO")
                            else:
                                outputDir = self.outputDir + 'results_' + self.campaign_name + '_' + curCampaign
                                f.write('mkdir -p '+outputDir+"/JOB"+str(iJob)+"/Sim_"+str(count) +'\n')
                                f.write('cp -f run_'+sh_name+'.sh'+' '+outputDir+'\n')
                                f.write('cp -f '+self.configurations_file+ ' ' +outputDir+'\n')
                                f.write("cd '"+self.local_path+"'"+"\n")
                                f.write("sleep $((11 + RANDOM % 50))"+"\n")
                                command1 = (
                                "python3 " + self.script +
                                " --"+self.outputDirName+"="+outputDir+"/JOB"+str(iJob)+'/Sim_' + str(count) +
                                " --"+self.seed+"="+str(jobRunSeed[iJob]))
                            command3 =(
                            " --"+curline+"="+self.doc['scenarioParameters'][curline][i]+
                            " --"+curline1+"="+self.doc['scenarioParameters'][curline1][i]+
                            " --"+curline2+"="+self.doc['scenarioParameters'][curline2][i]+
                            " --"+curCampaign+"="+varParam+
                            " > "+outputDir+"/JOB"+str(iJob)+'/Sim_' + str(count)+'.out 2>&1')
                            f.write(command1+self.commandScript+command3+'\n')
                            count = count + 1
            
            elif nOfCurlines == 4 and SimTied == 1 and nOfCurlinesTied == 2:
                with open('ListOfRandomNumbers.pkl', 'rb') as f:
                    jobRunSeed = pickle.load(f)
                curline = self.campaignLines[0]
                curline1 = self.campaignLines[1]
                curline2 = self.campaignLines[2]
                curline3 = self.campaignLines[3]
                count=0
                for i in range(len(self.doc['scenarioParameters'][curline])):
                    for k in range(len(self.doc['scenarioParameters'][curline2])):
                        for n in range(len(self.doc['scenarioParameters'][curline3])):
                            for varParam in self.doc['scenarioParameters'][curCampaign]:
                                sh_name = self.campaign_name + '_' + self.simLocation + '_' + curCampaign + '_JOB' + str(iJob) + '_Sim_' + str(count)
                                print(curCampaign+" campaign written in file: " 'run_%s.sh' % sh_name)
                                with open('run_%s.sh' % sh_name, 'w') as f:
                                    f.write('#!/bin/bash\n')
                                    if self.simLocation == 'cluster' or self.simLocation == 'service' or self.simLocation == 'intel-512' or self.simLocation == 'intel-256':
                                        print("TODO")
                                    else:
                                        outputDir = self.outputDir + 'results_' + self.campaign_name + '_' + curCampaign
                                        f.write('mkdir -p '+outputDir+"/JOB"+str(iJob)+"/Sim_"+str(count) +'\n')
                                        f.write('cp -f run_'+sh_name+'.sh'+' '+outputDir+'\n')
                                        f.write('cp -f '+self.configurations_file+ ' ' +outputDir+'\n')
                                        f.write("cd '"+self.local_path+"'"+"\n")
                                        f.write("sleep $((11 + RANDOM % 50))"+"\n")
                                        command1 = (
                                        "python3 " + self.script +
                                        " --"+self.outputDirName+"="+outputDir+"/JOB"+str(iJob)+'/Sim_' + str(count) +
                                        " --"+self.seed+"="+str(jobRunSeed[iJob]))
                                    command3 =(
                                    " --"+curline+"="+self.doc['scenarioParameters'][curline][i]+
                                    " --"+curline1+"="+self.doc['scenarioParameters'][curline1][i]+
                                    " --"+curline2+"="+self.doc['scenarioParameters'][curline2][k]+
                                    " --"+curline3+"="+self.doc['scenarioParameters'][curline3][n]+
                                    " --"+curCampaign+"="+varParam+
                                    "' > "+outputDir+"/JOB"+str(iJob)+'/Sim_' + str(count)+'.out 2>&1')
                                    f.write(command1+self.commandScript+command3+'\n')
                                    count = count + 1
            
            elif nOfCurlines == 5 and SimTied == 1 and nOfCurlinesTied == 2:
                with open('ListOfRandomNumbers.pkl', 'rb') as f:
                    jobRunSeed = pickle.load(f)
                curline = self.campaignLines[0]
                curline1 = self.campaignLines[1]
                curline2 = self.campaignLines[2]
                curline3 = self.campaignLines[3]
                curline4 = self.campaignLines[4]
                count=0
                for i in range(len(self.doc['scenarioParameters'][curline])):
                    for k in range(len(self.doc['scenarioParameters'][curline2])):
                        for n in range(len(self.doc['scenarioParameters'][curline3])):
                            for h in range(len(self.doc['scenarioParameters'][curline4])):
                                for varParam in self.doc['scenarioParameters'][curCampaign]:
                                    sh_name = self.campaign_name + '_' + self.simLocation + '_' + curCampaign + '_JOB' + str(iJob) + '_Sim_' + str(count)
                                    print(curCampaign+" campaign written in file: " 'run_%s.sh' % sh_name)
                                    with open('run_%s.sh' % sh_name, 'w') as f:
                                        f.write('#!/bin/bash\n')
                                        if self.simLocation == 'cluster' or self.simLocation == 'service' or self.simLocation == 'intel-512' or self.simLocation == 'intel-256':
                                            print("TODO")
                                        else:
                                            outputDir = self.outputDir + 'results_' + self.campaign_name + '_' + curCampaign
                                            f.write('mkdir -p '+outputDir+"/JOB"+str(iJob)+"/Sim_"+str(count) +'\n')
                                            f.write('cp -f run_'+sh_name+'.sh'+' '+outputDir+'\n')
                                            f.write('cp -f '+self.configurations_file+ ' ' +outputDir+'\n')
                                            f.write("cd '"+self.local_path+"'"+"\n")
                                            f.write("sleep $((11 + RANDOM % 50))"+"\n")
                                            command1 = (
                                            "python3 " + self.script +
                                            " --"+self.outputDirName+"="+outputDir +
                                            " --"+self.seed+"="+str(jobRunSeed[iJob]))
                                        command3 =(
                                        " --"+curline+"="+self.doc['scenarioParameters'][curline][i]+
                                        " --"+curline1+"="+self.doc['scenarioParameters'][curline1][i]+
                                        " --"+curline2+"="+self.doc['scenarioParameters'][curline2][k]+
                                        " --"+curline3+"="+self.doc['scenarioParameters'][curline3][n]+
                                        " --"+curline4+"="+self.doc['scenarioParameters'][curline4][h]+
                                        " --"+curCampaign+"="+varParam+
                                        "' > "+outputDir+"/JOB"+str(iJob)+'/Sim_' + str(count)+'.out 2>&1')
                                        f.write(command1+self.commandScript+command3+'\n')
                                        count = count + 1

            #f.write('wait')
                                                

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--file", type=str, help='Configuration File')
args = parser.parse_args()

configurations_file = args.file; 
with open(configurations_file, 'r') as f:
    doc = yaml.load(f, Loader=yaml.loader.BaseLoader)
    campaign_name = os.path.splitext(configurations_file)[0]
"""
doc = {'ScriptParameters': {'script': 'odc_placement_parser', 
                            'local_path': '/home/ubuntu/EmbrapiiCPqD/OpenRanDatacenterPlacement/open_ran_datacenter_placement/', 
                            'cluster_path': '/home/drdluna/', 
                            'CampaignTag': 'teste', 
                            'simLocation': 'local'}, 
       'ShellScriptParameters': {'nOfCurlines': '3', 
                                 'SimTied': '1', 
                                 'nOfCurlinesTied': '3', 
                                 'daytime': '1', 
                                 'htime': '12', 
                                 'ntasks': '8', 
                                 'cpusPerTask': '16', 
                                 'numberOfJobsShellScript': '5'}, 
       'campaignLines': {'campaignX': ['odcs'], 
                         'campaignLines': ['wcpu', 'wodc', 'wd'], 
                         'jobs': '100'}, 
       'scenarioParameters': {'cpuper100': ['14'], 
                              'maxdistance': ['11'], 
                              'capacity': ['1000'], 
                              'odcs': ['0', '27', '18', '13'], 
                              'trials': ['60'], 
                              'population': ['300'], 
                              'process': ['8'], 
                              'wcpu': ['0', '0'], 
                              'wodc': ['0', '0.5'], 
                              'wd': ['1', '0.5'], 
                              'seed': ['seed'], 
                              'csv': ['/home/ubuntu/EmbrapiiCPqD/OpenRanDatacenterPlacement/open_ran_datacenter_placement/CityData/Natal.csv'], 
                              'outputDir': ['/home/ubuntu/EmbrapiiCPqD/OpenRanDatacenterPlacement/open_ran_datacenter_placement/']}}

configurations_file = "Placement_Case_1_2.yaml"

"""
print (doc)
print('Simulação escolhida: ')
campaign = doc['campaignLines']['campaignX']
print(campaign)
                 
simu = Simulation(configurations_file)

for simC in campaign:
    simu.runCampaign(simC)
    

import argparse


class SimulationConfig:
    def __init__(self):
        self._parse_args()

    def _parse_args(self):
        parser = argparse.ArgumentParser()
        # problem args
        parser.add_argument("-c", "--cpuper100", type=int, default=14, help='cpus per 100MHz')
        parser.add_argument("-d", "--maxdistance", type=int, default=11, help='Max distance')
        parser.add_argument("-cp", "--capacity", type=int,default=50, help='Max capacity')
        parser.add_argument("-o", "--odcs", type=int, default=3, help='No. of Initial ODCs')
        #GA parameters
        parser.add_argument("-t", "--gen", type=int, default=60, help='no. of generations"')
        parser.add_argument("-pop", "--population", type=int, default=100, help='Population Size')
        parser.add_argument("-p", "--process", type=int, default=8, help='No. of Process')    
        # sum of weights must be 1
        # parser.add_argument("-wcpu", "--wcpu", type=float, default=1, help='Weight of CPUs per ODC')
        # parser.add_argument("-wodc", "--wodc", type=float, default=0, help='Weight of no. of ODCs')
        # parser.add_argument("-wd", "--wd", type=float, default=0, help='Weight of ORU-ODC distance')    
        #Sim parameters
        parser.add_argument("-s", "--seed", type=int, default=3758522074, help='Random State Seed')
        parser.add_argument("-csv", "--csv", type=str, default='/home/mbpaiva/Repositories/AITORAN/Open RAN Data Center Placement/open_ran_datacenter_placement/data/Test.csv', help='Full path where the processed .csvs are')
        parser.add_argument("-opd", "--outputDir", type=str, default='./visualization/output/', help='Full path where the results will be saved')
        # parser.add_argument("-gif", "--gif", action="store_true", help="Create a GIF of the optimization process")

        args = parser.parse_args()

        self.cpu_per_100mhz = args.cpuper100
        self.max_distance = args.maxdistance
        self.max_capacity = args.capacity
        self.num_odcs = args.odcs
        self.num_gen = args.gen
        self.population_size = args.population
        self.no_processes = args.process
        # self.obj_weights = [args.wcpu, args.wodc, args.wd]
        self.seed = args.seed
        self.dataset = args.csv
        self.output_dir = args.outputDir
        # self.gif = args.gif

        print("#### Sim Parameters ####")
        print("## Problem Parameters ##")
        print("     cpu_per_100mhz: ", self.cpu_per_100mhz)
        print("     max_distance: ", self.max_distance)
        print("     max_capacity: ", self.max_capacity)
        print("     num_initial_odcs (if 0 means ODCs = RUs): ", self.num_odcs)
        print("## NSGAII Parameters ##")
        print("     num_trials: ", self.num_gen)
        print("     population_size: ", self.population_size)
        print("     no_processes: ", self.no_processes)
        # print("     obj_weights: ", self.obj_weights)
        print("## Sim Parameters ##")
        print("     seed: ", self.seed)
        print("     dataset: ", self.dataset)
        print("     outputDir: ", self.output_dir)
        # print("     gif: ", self.gif)
        print("########################")
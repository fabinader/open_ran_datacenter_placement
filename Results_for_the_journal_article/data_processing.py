import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


path = '/home/mbpaiva/Repositories/AUTORAN/Case3'
analysis = 'Test'

SIM_DICT = [
    {'prob': 3, 'granu': 9},
    # {'prob': 4, 'granu': 9, 'city': 'Manaus'},
    {'prob': 4, 'granu': 9},
    # {'prob': 4, 'granu': 9, 'city': 'Natal'}
]

def parser_string(w0, w1, w2, prob):
    weights = f"{w0:.1f},{w1:.1f},{w2:.1f}"
    campaign_name = f"Case{prob}_{weights}"
    return campaign_name

def generate_campaign_name(w0,w1,w2,prob):
  args = []

  for i in range(len(w0)):
    arg = parser_string(w0[i],w1[i],w2[i],prob)
    args.append(arg)

  return args

def generate_all_campaign_case(prob, granu):
    if prob == 3:
        w0 = np.zeros(granu)
        w1 = np.linspace(0.1, 0.9, granu)
        w2 = 1 - w1
        args = generate_campaign_name(w0, w1, w2, prob)

    elif prob == 4:
        w0 = [0.1]*8 + [0.3]*5 + [0.5]*4 + [0.7]*2 + [0.8]
        w1 = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.1, 0.2, 0.3, 0.5, 0.6, 0.1, 0.2, 0.3, 0.4, 0.1, 0.2, 0.1]
        w2 = [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.6, 0.5, 0.4, 0.2, 0.1, 0.4, 0.3, 0.2, 0.1, 0.2, 0.1, 0.1]
        args = generate_campaign_name(w0, w1, w2, prob)

    return args

def generate_labels(prob, granu):
    if prob == 3:
        w0 = np.zeros(granu)
        w1 = np.linspace(0.1, 0.9, granu)
        w2 = 1 - w1
        return w0, w1, w2

    elif prob == 4:
        w0 = [0.1]*8 + [0.3]*5 + [0.5]*4 + [0.7]*2 + [0.8]
        w1 = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.1, 0.2, 0.3, 0.5, 0.6, 0.1, 0.2, 0.3, 0.4, 0.1, 0.2, 0.1]
        w2 = [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.6, 0.5, 0.4, 0.2, 0.1, 0.4, 0.3, 0.2, 0.1, 0.2, 0.1, 0.1]
        return w0, w1, w2
    else:
        return 'Problem Option Invalid'

def plot_3d(df, label1, label2, z_label, title):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # Plotando as duas curvas
    ax.plot(df['X'], df['Y'], df[label1], label=label1, marker='o')
    ax.plot(df['X'], df['Y'], df[label2], label=label2, marker='^')

    # Configurando rótulos e título
    ax.set_xlabel('w1')
    ax.set_ylabel('w2')
    ax.set_zlabel(z_label)
    ax.set_title(title)
    ax.legend()

    # Exibindo o gráfico
    plt.show()

def main():
    # CASE 3 =======================================================================
    listOdcsManaus = []
    listOdcsNatal = []
    listTotalCapacityManaus = []
    listTotalCapacityNatal = []
    listFiberLengthManaus = []
    listFiberLengthNatal = []
    listCapacityPerODCManaus = []
    listCapacityPerODCNatal = []
    num_jobs = 100

    weights = generate_all_campaign_case(SIM_DICT[0]['prob'], SIM_DICT[0]['granu'])

    for weight in weights:
        noOdcsManaus = []
        noOdcsNatal = []
        listCapacityManaus = []
        listCapacityNatal = []
        FiberLengthManaus = []
        FiberLengthNatal = []
        CapacityPerODCManaus = []
        CapacityPerODCNatal = []

        for job in range(num_jobs):
            base_path_Manaus = f'{path}/Campaign_Manaus{weight}/data/Job{job+1}/'
            base_path_Natal =  f'{path}/Campaign_Natal{weight}/data/Job{job+1}/'

            # Read the current capacities for Manaus and Natal
            dfManausCurrent_capacities = pd.read_csv(base_path_Manaus + 'df_capacities.csv', usecols=['odc_locations','capacities'])
            dfManausCurrent_capacities = dfManausCurrent_capacities.rename(columns={"odc_locations":"odc_locations_study"+str(weight),"capacities": "capacities_study"+str(weight)})

            dfNatalCurrent_capacities = pd.read_csv(base_path_Natal + 'df_capacities.csv', usecols=['odc_locations','capacities'])
            dfNatalCurrent_capacities = dfNatalCurrent_capacities.rename(columns={"odc_locations":"odc_locations_study"+str(weight),"capacities": "capacities_study"+str(weight)})

            # Read the current fiber length for Manaus and Natal
            dfManausCurrent_fiber = pd.read_csv(base_path_Manaus + '/df_fiberlength.csv', usecols=['odc_locations','fiberlength'])
            dfManausCurrent_fiber = dfManausCurrent_fiber.rename(columns={"odc_locations":"odc_locations_study"+str(weight),"fiberlength": "fiberlength_study"+str(weight)})

            dfNatalCurrent_fiber = pd.read_csv(base_path_Natal + '/df_fiberlength.csv',usecols=['odc_locations','fiberlength'])
            dfNatalCurrent_fiber = dfNatalCurrent_fiber.rename(columns={"odc_locations":"odc_locations_study"+str(weight),"fiberlength": "fiberlength_study"+str(weight)})

            # Read the current ODCs for Manaus and Natal
            dfManausCurrent_odcs = pd.read_csv(base_path_Manaus + '/df_client_association.csv', usecols=['odc_location','oru'])
            dfManausCurrent_odcs = dfManausCurrent_odcs.rename(columns={"odc_location":"odc_locations_study"+str(weight),"oru": "oru_study"+str(weight)})

            dfNatalCurrent_odcs = pd.read_csv(base_path_Natal + '/df_client_association.csv',usecols=['odc_location','oru'])
            dfNatalCurrent_odcs = dfNatalCurrent_odcs.rename(columns={"odc_location":"odc_locations_study"+str(weight),"oru": "oru_study"+str(weight)})

            # Calculate the average number of ODCs
            noOdcsManaus.append(dfManausCurrent_capacities.shape[0])
            noOdcsNatal.append(dfNatalCurrent_capacities.shape[0])

            # Calculate total number of CPUs for each city 
            listCapacityManaus.append(dfManausCurrent_capacities["capacities_study"+str(weight)].sum())
            listCapacityNatal.append(dfNatalCurrent_capacities["capacities_study"+str(weight)].sum())

            CapacityPerODCManaus.append(dfManausCurrent_capacities["capacities_study"+str(weight)].sum()/dfManausCurrent_capacities.shape[0])
            CapacityPerODCNatal.append(dfNatalCurrent_capacities["capacities_study"+str(weight)].sum()/dfNatalCurrent_capacities.shape[0])

            FiberLengthManaus.append(dfManausCurrent_fiber["fiberlength_study"+str(weight)].sum())
            FiberLengthNatal.append(dfNatalCurrent_fiber["fiberlength_study"+str(weight)].sum())

        listOdcsManaus.append(sum(noOdcsManaus)/len(noOdcsManaus))
        listOdcsNatal.append(sum(noOdcsNatal)/len(noOdcsNatal))

        listTotalCapacityManaus.append(sum(listCapacityManaus)/len(listCapacityManaus))  # List of Total Capacities for each cenario in Manaus
        listTotalCapacityNatal.append(sum(listCapacityNatal)/len(listCapacityNatal))  # List of Total Capacities for each cenario in Natal

        listCapacityPerODCManaus.append(sum(CapacityPerODCManaus)/len(CapacityPerODCManaus))
        listCapacityPerODCNatal.append(sum(CapacityPerODCNatal)/len(CapacityPerODCNatal))

        listFiberLengthManaus.append(sum(FiberLengthManaus)/len(FiberLengthManaus))
        listFiberLengthNatal.append(sum(FiberLengthNatal)/len(FiberLengthNatal))

    # Plotting the Results
    w0, w1, w2 = generate_labels(3, 9)

    data_NoODCs = {
        'X': w1,
        'Y': w2,
        'NoODCs-Manaus':listOdcsManaus,
        'NoODCs-Natal':listOdcsNatal
    }

    data_TotalCapacity = {
        'X': w1,
        'Y': w2,
        'TotalCapacity-Manaus':listTotalCapacityManaus,
        'TotalCapacity-Natal':listTotalCapacityNatal
    }

    data_CapacityPerODC = {
        'X': w1,
        'Y': w2,
        'CapacityPerODC-Manaus':listCapacityPerODCManaus,
        'CapacityPerODC-Natal':listCapacityPerODCNatal
    }

    data_FiberLength = {
        'X': w1,
        'Y': w2,
        'FiberLength-Manaus':listFiberLengthManaus,
        'FiberLength-Natal':listFiberLengthNatal
    }

    dfNoODCs = pd.DataFrame(data_NoODCs)
    dfTotalCapacity = pd.DataFrame(data_TotalCapacity)
    dfCapacityPerODC = pd.DataFrame(data_CapacityPerODC)
    dfFiberLength = pd.DataFrame(data_FiberLength)

    plot_3d(dfNoODCs, 'NoODCs-Manaus', 'NoODCs-Natal', 'No. ODCs (ODCs)', 'Número Médio de ODCs - w0 = 0, ODC = O-RUs')
    plot_3d(dfTotalCapacity, 'TotalCapacity-Manaus', 'TotalCapacity-Natal', 'Total Capacity (CPUs)', 'Capacidade Total - w0 = 0, ODC = O-RUs')
    plot_3d(dfCapacityPerODC, 'CapacityPerODC-Manaus', 'CapacityPerODC-Natal', 'Capacity (CPUs/ODCs)', 'Capacidade por ODCs - w0 = 0, ODC = O-RUs')
    plot_3d(dfFiberLength, 'FiberLength-Manaus', 'FiberLength-Natal', 'Fiber Length (km)', 'Comprimento Total de Fibra Óptica Médio - w0 = 0, ODC = O-RUs')

    # CASE 4 =======================================================================    
    num_jobs = 100
    
    weights = generate_all_campaign_case(SIM_DICT[1]['prob'], SIM_DICT[1]['granu'])
    path4 = '/home/mbpaiva/Repositories/AUTORAN/Case4'
    w0, w1, w2 = generate_labels(4, 9)
    count01 = 0
    count03 = 0
    count05 = 0
    count07 = 0
    count08 = 0
    listOdcsManaus = np.zeros([5,len(w0)])
    listOdcsNatal = np.zeros([5,len(w0)])
    listTotalCapacityManaus = np.zeros([5,len(w0)])
    listTotalCapacityNatal = np.zeros([5,len(w0)])
    listCapacityPerODCManaus = np.zeros([5,len(w0)])
    listCapacityPerODCNatal = np.zeros([5,len(w0)])
    listFiberLengthManaus = np.zeros([5,len(w0)])
    listFiberLengthNatal = np.zeros([5,len(w0)])

    for index, weight in enumerate(weights):
        noOdcsManaus = []
        noOdcsNatal = []
        listCapacityManaus = []
        listCapacityNatal = []
        CapacityPerODCManaus = []
        CapacityPerODCNatal = []
        FiberLengthManaus = []
        FiberLengthNatal = []

        for job in range(num_jobs):
            base_path_Manaus = f'{path4}/Campaign_Manaus{weight}/data/Job{job+1}/'
            base_path_Natal =  f'{path4}/Campaign_Natal{weight}/data/Job{job+1}/'

            # Read the current capacities for Manaus and Natal
            dfManausCurrent_capacities = pd.read_csv(base_path_Manaus + 'df_capacities.csv', usecols=['odc_locations','capacities'])
            dfManausCurrent_capacities = dfManausCurrent_capacities.rename(columns={"odc_locations":"odc_locations_study"+str(weight),"capacities": "capacities_study"+str(weight)})

            dfNatalCurrent_capacities = pd.read_csv(base_path_Natal + 'df_capacities.csv', usecols=['odc_locations','capacities'])
            dfNatalCurrent_capacities = dfNatalCurrent_capacities.rename(columns={"odc_locations":"odc_locations_study"+str(weight),"capacities": "capacities_study"+str(weight)})

            # Read the current fiber length for Manaus and Natal
            dfManausCurrent_fiber = pd.read_csv(base_path_Manaus + '/df_fiberlength.csv', usecols=['odc_locations','fiberlength'])
            dfManausCurrent_fiber = dfManausCurrent_fiber.rename(columns={"odc_locations":"odc_locations_study"+str(weight),"fiberlength": "fiberlength_study"+str(weight)})

            dfNatalCurrent_fiber = pd.read_csv(base_path_Natal + '/df_fiberlength.csv',usecols=['odc_locations','fiberlength'])
            dfNatalCurrent_fiber = dfNatalCurrent_fiber.rename(columns={"odc_locations":"odc_locations_study"+str(weight),"fiberlength": "fiberlength_study"+str(weight)})

            # Read the current ODCs for Manaus and Natal
            dfManausCurrent_odcs = pd.read_csv(base_path_Manaus + '/df_client_association.csv', usecols=['odc_location','oru'])
            dfManausCurrent_odcs = dfManausCurrent_odcs.rename(columns={"odc_location":"odc_locations_study"+str(weight),"oru": "oru_study"+str(weight)})

            dfNatalCurrent_odcs = pd.read_csv(base_path_Natal + '/df_client_association.csv',usecols=['odc_location','oru'])
            dfNatalCurrent_odcs = dfNatalCurrent_odcs.rename(columns={"odc_location":"odc_locations_study"+str(weight),"oru": "oru_study"+str(weight)})

            # Calculate the average number of ODCs
            noOdcsManaus.append(dfManausCurrent_capacities.shape[0])
            noOdcsNatal.append(dfNatalCurrent_capacities.shape[0])

            # Calculate total number of CPUs for each city 
            listCapacityManaus.append(dfManausCurrent_capacities["capacities_study"+str(weight)].sum())
            listCapacityNatal.append(dfNatalCurrent_capacities["capacities_study"+str(weight)].sum())

            CapacityPerODCManaus.append(dfManausCurrent_capacities["capacities_study"+str(weight)].sum()/dfManausCurrent_capacities.shape[0])
            CapacityPerODCNatal.append(dfNatalCurrent_capacities["capacities_study"+str(weight)].sum()/dfNatalCurrent_capacities.shape[0])

            # Calculate Fiber Length
            FiberLengthManaus.append(dfManausCurrent_fiber["fiberlength_study"+str(weight)].sum())
            FiberLengthNatal.append(dfNatalCurrent_fiber["fiberlength_study"+str(weight)].sum())

        if w0[index] == 0.1:
            # No. ODC
            listOdcsManaus[0,count01] = sum(noOdcsManaus)/len(noOdcsManaus)
            listOdcsNatal[0,count01] = sum(noOdcsNatal)/len(noOdcsNatal)
            # Capacity
            listTotalCapacityManaus[0,count01] = sum(listCapacityManaus)/len(listCapacityManaus)
            listTotalCapacityNatal[0,count01] = sum(listCapacityNatal)/len(listCapacityNatal)

            listCapacityPerODCManaus[0,count01] = sum(CapacityPerODCManaus)/len(CapacityPerODCManaus)
            listCapacityPerODCNatal[0,count01] = sum(CapacityPerODCNatal)/len(CapacityPerODCNatal)

            # Fiber Length
            listFiberLengthManaus[0,count01] = sum(FiberLengthManaus)/len(FiberLengthManaus)
            listFiberLengthNatal[0,count01] = sum(FiberLengthNatal)/len(FiberLengthNatal)

            count01 += 1
        elif w0[index] == 0.3:
            # No. ODC
            listOdcsManaus[1,count03] = sum(noOdcsManaus)/len(noOdcsManaus)
            listOdcsNatal[1,count03] = sum(noOdcsNatal)/len(noOdcsNatal)
            # Capacity
            listTotalCapacityManaus[1,count03] = sum(listCapacityManaus)/len(listCapacityManaus)
            listTotalCapacityNatal[1,count03] = sum(listCapacityNatal)/len(listCapacityNatal)

            listCapacityPerODCManaus[1,count03] = sum(CapacityPerODCManaus)/len(CapacityPerODCManaus)
            listCapacityPerODCNatal[1,count03] = sum(CapacityPerODCNatal)/len(CapacityPerODCNatal)

            # Fiber Length
            listFiberLengthManaus[1,count03] = sum(FiberLengthManaus)/len(FiberLengthManaus)
            listFiberLengthNatal[1,count03] = sum(FiberLengthNatal)/len(FiberLengthNatal)

            count03 += 1
        elif w0[index] == 0.5:
            # No. ODC
            listOdcsManaus[2,count05] = sum(noOdcsManaus)/len(noOdcsManaus)
            listOdcsNatal[2,count05] = sum(noOdcsNatal)/len(noOdcsNatal)
            # Capacity
            listTotalCapacityManaus[2,count05] = sum(listCapacityManaus)/len(listCapacityManaus)
            listTotalCapacityNatal[2,count05] = sum(listCapacityNatal)/len(listCapacityNatal)

            listCapacityPerODCManaus[2,count05] = sum(CapacityPerODCManaus)/len(CapacityPerODCManaus)
            listCapacityPerODCNatal[2,count05] = sum(CapacityPerODCNatal)/len(CapacityPerODCNatal)

            # Fiber Length
            listFiberLengthManaus[2,count05] = sum(FiberLengthManaus)/len(FiberLengthManaus)
            listFiberLengthNatal[2,count05] = sum(FiberLengthNatal)/len(FiberLengthNatal)

            count05 += 1
        elif w0[index] == 0.7:
            # No. ODC
            listOdcsManaus[3,count07] = sum(noOdcsManaus)/len(noOdcsManaus)
            listOdcsNatal[3,count07] = sum(noOdcsNatal)/len(noOdcsNatal)
            # Capacity
            listTotalCapacityManaus[3,count07] = sum(listCapacityManaus)/len(listCapacityManaus)
            listTotalCapacityNatal[3,count07] = sum(listCapacityNatal)/len(listCapacityNatal)

            listCapacityPerODCManaus[3,count07] = sum(CapacityPerODCManaus)/len(CapacityPerODCManaus)
            listCapacityPerODCNatal[3,count07] = sum(CapacityPerODCNatal)/len(CapacityPerODCNatal)

            # Fiber Length
            listFiberLengthManaus[3,count07] = sum(FiberLengthManaus)/len(FiberLengthManaus)
            listFiberLengthNatal[3,count07] = sum(FiberLengthNatal)/len(FiberLengthNatal)

            count07 += 1
        elif w0[index] == 0.8:
            # No. ODC
            listOdcsManaus[4,count08] = sum(noOdcsManaus)/len(noOdcsManaus)
            listOdcsNatal[4,count08] = sum(noOdcsNatal)/len(noOdcsNatal)
            # Capacity
            listTotalCapacityManaus[4,count08] = sum(listCapacityManaus)/len(listCapacityManaus)
            listTotalCapacityNatal[4,count08] = sum(listCapacityNatal)/len(listCapacityNatal)

            listCapacityPerODCManaus[4,count08] = sum(CapacityPerODCManaus)/len(CapacityPerODCManaus)
            listCapacityPerODCNatal[4,count08] = sum(CapacityPerODCNatal)/len(CapacityPerODCNatal)

            # Fiber Length
            listFiberLengthManaus[4,count08] = sum(FiberLengthManaus)/len(FiberLengthManaus)
            listFiberLengthNatal[4,count08] = sum(FiberLengthNatal)/len(FiberLengthNatal)

            count08 += 1

    data_NoODCs = {
        'X': w1,
        'Y': w2,
        'NoODCs-Manaus01':listOdcsManaus[0,:],
        'NoODCs-Natal01':listOdcsNatal[0,:],
        'NoODCs-Manaus03':listOdcsManaus[1,:],
        'NoODCs-Natal03':listOdcsNatal[1,:],
        'NoODCs-Manaus05':listOdcsManaus[2,:],
        'NoODCs-Natal05':listOdcsNatal[2,:],
        'NoODCs-Manaus07':listOdcsManaus[3,:],
        'NoODCs-Natal07':listOdcsNatal[3,:],
        'NoODCs-Manaus08':listOdcsManaus[4,:],
        'NoODCs-Natal08':listOdcsNatal[4,:],
    }

    data_TotalCapacity = {
        'X': w1,
        'Y': w2,
        'TotalCapacity-Manaus01':listTotalCapacityManaus[0,:],
        'TotalCapacity-Natal01':listTotalCapacityNatal[0,:],
        'TotalCapacity-Manaus03':listTotalCapacityManaus[1,:],
        'TotalCapacity-Natal03':listTotalCapacityNatal[1,:],
        'TotalCapacity-Manaus05':listTotalCapacityManaus[2,:],
        'TotalCapacity-Natal05':listTotalCapacityNatal[2,:],
        'TotalCapacity-Manaus07':listTotalCapacityManaus[3,:],
        'TotalCapacity-Natal07':listTotalCapacityNatal[3,:],
        'TotalCapacity-Manaus08':listTotalCapacityManaus[4,:],
        'TotalCapacity-Natal08':listTotalCapacityNatal[4,:],
    }

    data_CapacityPerODC = {
        'X': w1,
        'Y': w2,
        'CapacityPerODC-Manaus01':listCapacityPerODCManaus[0,:],
        'CapacityPerODC-Natal01':listCapacityPerODCNatal[0,:],
        'CapacityPerODC-Manaus03':listCapacityPerODCManaus[1,:],
        'CapacityPerODC-Natal03':listCapacityPerODCNatal[1,:],
        'CapacityPerODC-Manaus05':listCapacityPerODCManaus[2,:],
        'CapacityPerODC-Natal05':listCapacityPerODCNatal[2,:],
        'CapacityPerODC-Manaus07':listCapacityPerODCManaus[3,:],
        'CapacityPerODC-Natal07':listCapacityPerODCNatal[3,:],
        'CapacityPerODC-Manaus08':listCapacityPerODCManaus[4,:],
        'CapacityPerODC-Natal08':listCapacityPerODCNatal[4,:],
    }

    data_FiberLength = {
        'X': w1,
        'Y': w2,
        'FiberLength-Manaus01':listFiberLengthManaus[0,:],
        'FiberLength-Natal01':listFiberLengthNatal[0,:],
        'FiberLength-Manaus03':listFiberLengthManaus[1,:],
        'FiberLength-Natal03':listFiberLengthNatal[1,:],
        'FiberLength-Manaus05':listFiberLengthManaus[2,:],
        'FiberLength-Natal05':listFiberLengthNatal[2,:],
        'FiberLength-Manaus07':listFiberLengthManaus[3,:],
        'FiberLength-Natal07':listFiberLengthNatal[3,:],
        'FiberLength-Manaus08':listFiberLengthManaus[4,:],
        'FiberLength-Natal08':listFiberLengthNatal[4,:],
    }

    dfNoODCs = pd.DataFrame(data_NoODCs)
    dfTotalCapacity = pd.DataFrame(data_TotalCapacity)
    dfCapacityPerODC = pd.DataFrame(data_CapacityPerODC)
    dfFiberLength = pd.DataFrame(data_FiberLength)

    plot_3d(dfNoODCs, 'NoODCs-Manaus01', 'NoODCs-Natal01', 'No. ODCs (ODCs)', 'Número Médio de ODCs - w0 = 0.1, ODC = O-RUs')
    plot_3d(dfNoODCs, 'NoODCs-Manaus03', 'NoODCs-Natal03', 'No. ODCs (ODCs)', 'Número Médio de ODCs - w0 = 0.3, ODC = O-RUs')
    plot_3d(dfNoODCs, 'NoODCs-Manaus05', 'NoODCs-Natal05', 'No. ODCs (ODCs)', 'Número Médio de ODCs - w0 = 0.5, ODC = O-RUs')
    plot_3d(dfNoODCs, 'NoODCs-Manaus07', 'NoODCs-Natal07', 'No. ODCs (ODCs)', 'Número Médio de ODCs - w0 = 0.7, ODC = O-RUs')
    plot_3d(dfNoODCs, 'NoODCs-Manaus08', 'NoODCs-Natal08', 'No. ODCs (ODCs)', 'Número Médio de ODCs - w0 = 0.8, ODC = O-RUs')
    plot_3d(dfTotalCapacity, 'TotalCapacity-Manaus01', 'TotalCapacity-Natal01', 'Total Capacity (CPUs)', 'Capacidade Total - w0 = 0.1, ODC = O-RUs')
    plot_3d(dfTotalCapacity, 'TotalCapacity-Manaus03', 'TotalCapacity-Natal03', 'Total Capacity (CPUs)', 'Capacidade Total - w0 = 0.3, ODC = O-RUs')
    plot_3d(dfTotalCapacity, 'TotalCapacity-Manaus05', 'TotalCapacity-Natal05', 'Total Capacity (CPUs)', 'Capacidade Total - w0 = 0.5, ODC = O-RUs')
    plot_3d(dfTotalCapacity, 'TotalCapacity-Manaus07', 'TotalCapacity-Natal07', 'Total Capacity (CPUs)', 'Capacidade Total - w0 = 0.7, ODC = O-RUs')
    plot_3d(dfTotalCapacity, 'TotalCapacity-Manaus08', 'TotalCapacity-Natal08', 'Total Capacity (CPUs)', 'Capacidade Total - w0 = 0.8, ODC = O-RUs')
    plot_3d(dfCapacityPerODC, 'CapacityPerODC-Manaus01', 'CapacityPerODC-Natal01', 'Capacity (CPUs/ODCs)', 'Capacidade por ODCs - w0 = 0.1, ODC = O-RUs')
    plot_3d(dfCapacityPerODC, 'CapacityPerODC-Manaus03', 'CapacityPerODC-Natal03', 'Capacity (CPUs/ODCs)', 'Capacidade por ODCs - w0 = 0.3, ODC = O-RUs')
    plot_3d(dfCapacityPerODC, 'CapacityPerODC-Manaus05', 'CapacityPerODC-Natal05', 'Capacity (CPUs/ODCs)', 'Capacidade por ODCs - w0 = 0.5, ODC = O-RUs')
    plot_3d(dfCapacityPerODC, 'CapacityPerODC-Manaus07', 'CapacityPerODC-Natal07', 'Capacity (CPUs/ODCs)', 'Capacidade por ODCs - w0 = 0.7, ODC = O-RUs')
    plot_3d(dfCapacityPerODC, 'CapacityPerODC-Manaus08', 'CapacityPerODC-Natal08', 'Capacity (CPUs/ODCs)', 'Capacidade por ODCs - w0 = 0.8, ODC = O-RUs')
    plot_3d(dfFiberLength, 'FiberLength-Manaus01', 'FiberLength-Natal01', 'Fiber Length (km)', 'Comprimento Total de Fibra Óptica Médio - w0 = 0.1, ODC = O-RUs')
    plot_3d(dfFiberLength, 'FiberLength-Manaus03', 'FiberLength-Natal03', 'Fiber Length (km)', 'Comprimento Total de Fibra Óptica Médio - w0 = 0.3, ODC = O-RUs')
    plot_3d(dfFiberLength, 'FiberLength-Manaus05', 'FiberLength-Natal05', 'Fiber Length (km)', 'Comprimento Total de Fibra Óptica Médio - w0 = 0.5, ODC = O-RUs')
    plot_3d(dfFiberLength, 'FiberLength-Manaus07', 'FiberLength-Natal07', 'Fiber Length (km)', 'Comprimento Total de Fibra Óptica Médio - w0 = 0.7, ODC = O-RUs')
    plot_3d(dfFiberLength, 'FiberLength-Manaus08', 'FiberLength-Natal08', 'Fiber Length (km)', 'Comprimento Total de Fibra Óptica Médio - w0 = 0.8, ODC = O-RUs')


if __name__ == '__main__':
    main()
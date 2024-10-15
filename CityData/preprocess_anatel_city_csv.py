import pandas as pd
import argparse

# Set up argument parser
parser = argparse.ArgumentParser(description="Process CSV files for licenciamento.")
parser.add_argument('dataset', type=str, help="Dataset to read (e.g., 'Manaus.csv' or 'Natal.csv')")
parser.add_argument('output', type=str, help="Output filename (without extension)")

args = parser.parse_args()

# Read the dataset based on the provided argument
dataset = args.dataset
#output = args.output

df = pd.read_csv(dataset, encoding='latin-1')

# Specify the columns to keep and rename them
columns_to_keep = {
    'NumEstacao': 'cell_site_id',
    'DesignacaoEmissao': 'emission_designation',
    'Tecnologia': 'technology',
    'FreqTxMHz': 'tx_frequency',
    'FreqRxMHz': 'rx_frequency',
    'Azimute': 'azimuth',
    'GanhoAntena': 'antenna_gain',
    'FrenteCostaAntena': 'back_front_relation',
    'AnguloMeiaPotenciaAntena': 'hpa',
    'AnguloElevacao': 'mechanical_elevation',
    'Polarizacao': 'polarization',
    'AlturaAntena': 'antenna_height',
    'PotenciaTransmissorWatts': 'tx_power',
    'Latitude': 'latitude',
    'Longitude': 'longitude',
    '_id': 'cell_carrier_id',
    'NomeEntidade': 'operator'
}

# Keep only the specified columns and rename them
df = df[list(columns_to_keep.keys())]
df.rename(columns=columns_to_keep, inplace=True)

# Filter the DataFrame for the specific operator
filtered_df = df[df['operator'] == 'TELEFONICA BRASIL S.A.']

# Write the filtered DataFrame to the specified output file
output_filename = args.output
filtered_df.to_csv(output_filename + '.csv', index=False)

import pandas as pd

filename = "Manaus"
# Read the CSV file into a DataFrame
if filename == 'Manaus':
    df = pd.read_csv('csv_manaus_licenciamento_nr.csv', encoding='latin-1')
elif filename == 'Natal':
    df = pd.read_csv('csv_natal_licenciamento_nr.csv', encoding='latin-1')

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

# Display the filtered DataFrame
#print(filtered_df)

filtered_df.to_csv(filename+'.csv', index=False)
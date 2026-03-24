# import libraries
import pandas as pd

print('🔄 Reading data.py')

# set paths 
CUBO_PATH = r"data\cubo_1.xlsx"
CLUSTERS_PATH = r"data\clusters_bdg.xlsx"
VENTAS_FACT = r"data\Ventasxfacturas.csv"

# DF dictionary
data_dict = {}

def load_data():
    global data_dict
    data_dict = {
        "cubo_base": pd.read_excel(CUBO_PATH,
                                    sheet_name = 'cat4',
                                    skiprows=4,
                                    dtype={"COD_ARTICULO": str}
                                    ),
        "clusters": pd.read_excel(CLUSTERS_PATH),
        "ventasxfact": pd.read_csv(VENTAS_FACT, sep=",", 
                                        low_memory=False,
                                        dtype={"COD_ARTICULO": str}).reset_index(drop=True),
    }
    return data_dict

load_data()

print('✅ Data was succesfully loaded')


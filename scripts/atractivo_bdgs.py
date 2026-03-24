import pandas as pd
from .bronce_layer import data_dict

# Import DataSets
ventasxfact = data_dict["ventasxfact"]
cubo = data_dict["cubo_base"]
clusters = data_dict["clusters"]

# -----------------------------------------
# PRE-PROCESING DATA
# -----------------------------------------

#converting to string for merging
cubo['COD_ARTICULO'] = cubo['COD_ARTICULO'].astype(str)
ventasxfact['COD_ARTICULO'] = ventasxfact['COD_ARTICULO'].astype(str)

# Filtering only FARMACORP clusters
clusters_fc = clusters[clusters['UNE']=='FARMACORP']

#Selecting only registers on FARMACORP/ETICOS&OTC
cubo_fc = pd.merge(
    cubo,
    clusters_fc,
    left_on='COD_BODEGA',
    right_on='BODEGA'
)

# Filtering only necessary columns
cubo_cat4 = cubo_fc[['COD_ARTICULO', 'CAT 4']].drop_duplicates()

# Selecting only FARMACORP clusters 
ventasxfact = pd.merge(
  ventasxfact,
  clusters_fc,
  left_on='COD_BODEGA',
  right_on='BODEGA'
 )

# filtering only SKUs on FARMACORP
ventas_farmacia = pd.merge(cubo_cat4,
                            ventasxfact,
                            on='COD_ARTICULO',
                            how='inner'
                            )
# -----------------------------------------
# PRE-PROCESING DATA
# -----------------------------------------

# Counting number of unique invoices per Bodega
ventasxbdg = ventas_farmacia.groupby(
    'COD_BODEGA').agg({'NRO_FACTURAS':'nunique'}).reset_index()

# Counting number of unique invoices per CAT 4 and Bodega
ventasxcat = ventas_farmacia.groupby(
    ['CAT 4', 'COD_BODEGA']).agg({'NRO_FACTURAS':'nunique'}).reset_index()

# Merging both to calculate support per CAT 4 in each Bodega
ventas_cat_bdg = pd.merge(
    ventasxcat,
    ventasxbdg,
    on='COD_BODEGA',
    suffixes=('_CAT4', '_TOTAL_BDG')
)

# -----------------------------------------
# CALCULATING SUPPORT PER CAT 4
# -----------------------------------------
ventas_cat_bdg['support_cat4'] = ventas_cat_bdg['NRO_FACTURAS_CAT4'] / ventas_cat_bdg['NRO_FACTURAS_TOTAL_BDG']
ventas_cat_bdg = ventas_cat_bdg.sort_values(by=['COD_BODEGA', 'support_cat4'], ascending=[True, False])

ventas_cat_bdg = ventas_cat_bdg.groupby('COD_BODEGA').head(50)

# SUPPORT AyB

# selfmerge for finding pairs of CAT 4 on same invoice
pairs_factura = pd.merge(
    ventas_farmacia,
    ventas_farmacia,
    on=["NRO_FACTURAS", "COD_BODEGA"],
    suffixes=("_A", "_B")
)

# filtering combinations to avoid duplicates
pairs_factura = pairs_factura[pairs_factura["CAT 4_A"] != pairs_factura["CAT 4_B"]]

# keeping only one order of each pair
pairs_factura = pairs_factura[pairs_factura["CAT 4_A"] > pairs_factura["CAT 4_B"]]

# counting and ordering number of unique invoices per CAT 4 pair and Bodega
ventasABxbdg = pairs_factura.groupby(
    ['CAT 4_A', 'CAT 4_B', 'COD_BODEGA']
    ).agg({'NRO_FACTURAS':'nunique'}).reset_index()

ventasABxbdg.sort_values(
    by=['COD_BODEGA', 'NRO_FACTURAS'], 
    ascending=[True, False])

# merging with total invoices per Bodega to calculate support
ventasxpairs = pd.merge(
    ventasABxbdg,
    ventasxbdg,
    on='COD_BODEGA',
    suffixes=('_PAIR', '_TOTAL_BDG')
)

# counting and ordering number of unique invoices per CAT 4 pair and Bodega
ventasxpairs['support_AB'] = (ventasxpairs['NRO_FACTURAS_PAIR'] / 
                                ventasxpairs['NRO_FACTURAS_TOTAL_BDG']).round(8)

ventasxpairs.sort_values(by=['COD_BODEGA', 'NRO_FACTURAS_PAIR'], 
                            ascending=[True, False])

# Merging support per CAT 4 and support per CAT 4 pair
ventas_cat_bdg_pairs = pd.merge(
    ventas_cat_bdg[['CAT 4', 'COD_BODEGA', 'NRO_FACTURAS_CAT4', 'support_cat4']],
    ventasxpairs,
    left_on=['CAT 4', 'COD_BODEGA'],
    right_on=['CAT 4_A', 'COD_BODEGA'],
    #how='left'
)

# Merging to get support of CAT 4 B
ventas_pairs = pd.merge(
    ventas_cat_bdg_pairs[['COD_BODEGA', 'NRO_FACTURAS_CAT4', 
                            'support_cat4', 'CAT 4_A','CAT 4_B', 'NRO_FACTURAS_PAIR', 
                            'NRO_FACTURAS_TOTAL_BDG', 'support_AB']],
    ventas_cat_bdg[['CAT 4', 'COD_BODEGA', 'support_cat4', 'NRO_FACTURAS_CAT4']],
    left_on=['CAT 4_B', 'COD_BODEGA'],
    right_on=['CAT 4', 'COD_BODEGA'],
    #how='left',
    suffixes=['_A', '_B']
)

# selecting and ordering final columns
ventas_pairs = ventas_pairs[[
    'COD_BODEGA', 'CAT 4_A', 'CAT 4_B', 
    'NRO_FACTURAS_CAT4_A', 'NRO_FACTURAS_CAT4_B', 'NRO_FACTURAS_PAIR', 'NRO_FACTURAS_TOTAL_BDG', 
    'support_cat4_A', 'support_cat4_B', 'support_AB',
    
]]

# -----------------------------------------
# CALCULATING LAST INDICATORS
# -----------------------------------------

ventas_pairs['confidence_AB_A'] = (ventas_pairs['support_AB'] / ventas_pairs['support_cat4_A']).round(8)

ventas_pairs['lift_ABA_B'] = (ventas_pairs['confidence_AB_A'] / ventas_pairs['support_cat4_B']).round(8)

ventas_pairs = ventas_pairs.sort_values(by=['COD_BODEGA', 'support_cat4_A', 'confidence_AB_A'], ascending=[True,False, False])

ventasxcat = ventas_farmacia.groupby(['CAT 4', 'COD_BODEGA']).agg({'Ventas':'sum'}).reset_index()

# Merging to find total sales per CAT 4 B and Bodega
ventas_pairs = pd.merge(
    ventas_pairs,
    ventasxcat,
    left_on=['CAT 4_B', 'COD_BODEGA'],
    right_on=['CAT 4', 'COD_BODEGA'],
    how='left'
)

#Final order of the columns
ventas_pairs_fc = ventas_pairs[[
    'COD_BODEGA', 'CAT 4_A', 'CAT 4_B', 
    'NRO_FACTURAS_CAT4_A','NRO_FACTURAS_CAT4_B', 'NRO_FACTURAS_PAIR', 'NRO_FACTURAS_TOTAL_BDG',
    'support_cat4_A', 'support_cat4_B', 'support_AB', 'confidence_AB_A','lift_ABA_B', 'Ventas']].copy()

# -----------------------------------------
# EXPORT RESULTS
# ----------------------------------------

ventas_pairs_fc.to_excel(r"output\support_analysis_bdg.xlsx", index=False)
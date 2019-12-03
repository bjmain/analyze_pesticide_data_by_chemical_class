#!/usr/bin/python3
import pickle
import glob
import pandas as pd
from sqlalchemy import create_engine
import psycopg2
import config   #you need to create this config.py file and update the variables with your database, username and password

#import chem_plotter
import pylab as P

# Get a database connection
conn_string = "host="+config.HOST+" dbname="+config.DB+" user="+config.username+" password="+config.password

conn = psycopg2.connect(conn_string)

# Create a cursor object. Allows us to execute the SQL query
cursor = conn.cursor()

def load_data(schema, table, chem_list_tuple):
    sql_command = "SELECT * FROM {}.{} WHERE chem_code IN {};".format(str(schema), str(table), str(chem_list_tuple)) # get chem data
    # Load the data
    data = pd.read_sql(sql_command, conn)
    return (data)

#input chemical class datasheet
chem = pd.read_excel("Main_chemclass.xlsx", sheet_name="chemclass", converters={'CHEM_CODE':int, "CHEMNAME":str, "AI_CLASS":str})

# Organize chemicals by mode of action. 
# 1) Voltage-gated sodium channel
na_ch_pyr = chem[chem["AI_CLASS"]=="PYRETHROID"]
na_ch_OC = chem[chem["AI_CLASS"]=="ORGANOCHLORINE"]
botanical = [510,90510]   #pyrethrins
na_ch_botanical = chem[chem["CHEM_CODE"].isin(botanical)]

# combine data from classes with the same mode of action
all_sodium_channel = pd.concat([na_ch_pyr, na_ch_OC, na_ch_botanical])
sodium_channel_chem_codes = tuple(list(all_sodium_channel['CHEM_CODE'])) # NOTE: Prod_no is not listed in the chem_class sheet, so if we want to sort by product, we need to convert prod_no to CHEM_CODE

# Get select data from database
sodium_df = load_data("gateway","dpr_pur.use_data_chemical", sodium_channel_chem_codes)
print("NA_channel#", len(sodium_df))
# NOTE: Once you load the data into this pickle, you can comment out the data download part and start reading in the pickle for quicker analysis.
sodium_df.to_pickle("sodium_channel_data.pkl")  # save DF for easy plotting later


# 2) AChE inhibitors
AChE_OP = chem[chem["AI_CLASS"]=="ORGANOPHOSPHATE"]
carbamate = ["CARBAMATE", "CARBAMATE_OTHER"]
AChE_carbamate = chem[chem["AI_CLASS"].isin(carbamate)]

# combine data from classes with the same mode of action
all_AChE = pd.concat([AChE_OP,AChE_carbamate])
AChE_inhibitor_chem_codes = tuple(list(all_AChE['CHEM_CODE']))
 
# Get select data from database
AChE_df = load_data("gateway","dpr_pur.use_data_chemical", AChE_inhibitor_chem_codes)
print("AChE#", len(AChE_df))
AChE_df.to_pickle("AChE_data.pkl")  # save DF for easy plotting later

#set up your figure for plotting
fig1 = P.figure(num=None, figsize=(16, 8), dpi=80, facecolor='w', edgecolor='k')
ax1 = fig1.add_subplot(111)

#Sodium Channel data
df = pd.read_pickle("sodium_channel_data.pkl")
df = df[df["unit_treated"]=="A"] # I still need to convert non-acre units to acres.
df.to_pickle("sodium_channel_data_acre.pkl")
df['year'] = pd.DatetimeIndex(df['applic_dt']).year
sodium_acre_yr = df.groupby("year", as_index=False).sum()
sodium_acre_yr.to_pickle("sodium_channel_data_acre_yr.pkl")
df = pd.read_pickle("sodium_channel_data_acre_yr.pkl")

df.plot(kind='line',x='year',y='acre_treated',color='red', label="Sodium", ax=ax1)

#AChE Data
df2 = pd.read_pickle("AChE_data.pkl")
df2 = df2[df2["unit_treated"]=="A"] # I still need to convert non-acre units to acres.
df2.to_pickle("AChE_data_acre.pkl")
df2['year'] = pd.DatetimeIndex(df2['applic_dt']).year
ache_acre_yr = df2.groupby("year", as_index=False).sum()
ache_acre_yr.to_pickle("AChE_data_acre_yr.pkl")
df = pd.read_pickle("AChE_data_acre.pkl")
df2 = pd.read_pickle("AChE_data_acre_yr.pkl")

df2.plot(kind='line',x='year',y='acre_treated',color='black', label="AChE",ax=ax1)

P.legend()
P.ylabel("acres treated")
P.show()

import pandas as pd
import data_cleaning as dc
import google_sheets_update as gupdate


cibfile =r"D:\\dev\\jövedelem\\src\\cib április.xls"
granitfile=r"D:\\dev\\jövedelem\\src\\granit_április.xml"

cib_data=dc.cib_process(cibfile)
granit_data=dc.granit_process(granitfile)

all_data=(pd.concat([cib_data,granit_data])
            .reset_index(drop=True))

all_data["Összeg"]=all_data["Összeg"].astype(float)
all_data["DÁTUM"]=pd.to_datetime(all_data["DÁTUM"])
#all_data.to_csv(r"D:\\dev\\jövedelem\\all_data.csv")

all_data=gupdate.gdrive_process(all_data)









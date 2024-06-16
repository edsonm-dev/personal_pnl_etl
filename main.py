import pandas as pd
import data_cleaning as dc
import google_sheets_update as gupdate

def main():
    

    bank1_data=dc.bank1_process(r"D:\\dev\\portfolio\\expense report etl\\src\\bank1_2023_march.xls")
    bank2_data=dc.bank2_process(r"D:\\dev\\portfolio\\expense report etl\\src\\bank2_2023_march.xml")


    with pd.concat([bank1_data,bank2_data]).reset_index(drop=True) as all_data:

        all_data["AMOUNT"]=all_data["AMOUNT"].astype(float)
        all_data["DATE"]=pd.to_datetime(all_data["DATE"])
    #all_data.to_csv(r"D:\\dev\\jövedelem\\all_data.csv")

        gupdate.gdrive_process(all_data)

    print("Transactions have been appended")

if __name__=="__main__":
    main()






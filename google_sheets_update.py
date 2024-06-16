import pandas as pd
import gspread 
from gspread_dataframe import set_with_dataframe,get_as_dataframe



gc = gspread.service_account(filename=r"D:\\private\\jovedelem-service account.json")


def  gdrive_process(data):

    transactionSheet=gc.open('Jövedelem').worksheet("Tranzakciók")

    lastrow=len(list(transactionSheet.col_values(1)))

    modifiedData=gdrive_expression_match(data)

    modifiedData['Kategória ID']=modifiedData['Kategória ID'].fillna(0).astype(int)
    modifiedData['Alkategória ID']=modifiedData['Alkategória ID'].fillna(0).astype(int) 



    set_with_dataframe(transactionSheet,modifiedData.iloc[:, :], row=lastrow+1, include_index=False, include_column_header=False, resize=False, allow_formulas=False)

    return None






def gdrive_expression_match(data):

    expressions=(get_as_dataframe(gc.open('Jövedelem').worksheet("Kifejezések"))
                .dropna(axis=0, how='all')
                .dropna(axis=1,how='all'))

    expression_dicts=expressions.to_dict(orient="records")
    
    data['Leírás']=data['Leírás'].astype(str)

    def searchexpression(desc,dicts):

        filtered_list = [d for d in dicts if d['LEÍRÁS'].lower() in desc.lower()]
    
        if len(filtered_list)==0 :
            filtered_list.append({'Kategória ID': 0, 'Alkategória ID': 0,'LEÍRÁS': 0})

        return pd.Series([filtered_list[0]['Kategória ID'],filtered_list[0]['Alkategória ID']])

    data[['Kategória ID','Alkategória ID']]=data.apply(lambda x: searchexpression(x['Leírás'],expression_dicts),axis=1)

    return data


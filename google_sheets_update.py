import pandas as pd
import gspread 
from gspread_dataframe import set_with_dataframe,get_as_dataframe


# to connect google drive and sheets i needed to setup the service account
gc = gspread.service_account(filename=r"D:\\private\\jovedelem-service account.json")


def  gdrive_process(data):

    
    transactionSheet=gc.open('revenue report').worksheet("Transactions")

    # getting the lastrow in the transactions sheet, as i want to append the data, not overwrite it
    lastrow=len(list(transactionSheet.col_values(1)))

    # categorizing the data based on expressions
    modifiedData=gdrive_expression_match(data)

    # returning zeroes, where the transactions couldn't be categorized
    modifiedData['CATEGORY ID']=modifiedData['CATEGORY ID'].fillna(0).astype(int)
    modifiedData['SUBCATEGORY ID']=modifiedData['SUBCATEGORY ID'].fillna(0).astype(int) 


    # appending
    set_with_dataframe(transactionSheet,modifiedData.iloc[:, :], row=lastrow+1, include_index=False, include_column_header=False, resize=False, allow_formulas=False)

    






def gdrive_expression_match(data):

    # this function checks if the expressions from the expressions sheet can be found in the data's DESCRIPTION field
    # if yes, then it updates the CATEGORY ID, SUBCATEGORY ID field accordingly

    expressions=(get_as_dataframe(gc.open('revenue report').worksheet("Expressions"))
                .dropna(axis=0, how='all')
                .dropna(axis=1,how='all'))

    expression_dicts=expressions.to_dict(orient="records")
    
    data['DESCRIPTION']=data['DESCRIPTION'].astype(str)

    def searchexpression(desc,dicts):
        
        filtered_list = [d for d in dicts if d['DESCRIPTION'].lower() in desc.lower()]
    
        if len(filtered_list)==0 :
            filtered_list.append({'CATEGORY ID': 0, 'SUBCATEGORY ID': 0,'DESCRIPTION': 0})

        return pd.Series([filtered_list[0]['CATEGORY ID'],filtered_list[0]['SUBCATEGORY ID']])

    data[['CATEGORY ID','SUBCATEGORY ID']]=data.apply(lambda x: searchexpression(x['DESCRIPTION'],expression_dicts),axis=1)

    return data



import pandas as pd
import xml.etree.ElementTree as ET
import re
pd.options.mode.chained_assignment = None

def bank1_process(bank1file):

  df= pd.read_excel(bank1file,skiprows=9)
      
  df=data_cleaning_bank1(df)
  
  # creating empty columns for category ids and providing the owner of the account    
  df[['CATEGORY ID', 'SUBCATEGORY ID',"OWNER"]]=["","","PersonX"]
      
  return df[["OWNER","DATE",'CATEGORY ID', 'SUBCATEGORY ID','DESCRIPTION','AMOUNT']]


def data_cleaning_bank1(df):
    

    # grouping and cutting the df into smaller dataframes based on the type of transaction field
    # the result is a dictionary that contains the dfs, key is the transaction type
    transactiongroups=df.groupby('TYPE OF TRANSACTION')

    smaller_dfs = {key: transactiongroups.get_group(key) for key in transactiongroups.groups}
    
    # in some cases, even if the description field is the same, the replacement can be different based on
    # the type of transaction field. so I keep patterns separate for each type of transactions
    replacements={
    'fees':{re.compile(r'^[\w\s\\,-]+$',re.IGNORECASE):"TRANSFER FEE"},
   
    'transfers':{re.compile(r'^[\d\s-]*',re.IGNORECASE):"Transfer Credit - ",
                 re.compile(r'\s',re.IGNORECASE):" "},

    'income':{re.compile(r'^[\d\s\-]*',re.IGNORECASE):"Salary - ",
              re.compile(r'Partnerek\sközti\segyedi\sazonosító:\s\w+$',re.IGNORECASE):"",
              re.compile(r'\sKözlemény[\w\s.:-]+$',re.IGNORECASE):""},
   
    'otherdebit':{re.compile(r'^[\w\s:,/-]*BLOCK OF FLATS[\w\s:,/-]*$',re.IGNORECASE):"COMMON COST",
                   re.compile(r'&&TF\d+',re.IGNORECASE):"MORTGAGE",
                   re.compile(r'^\d{8}-\d{8}-*\d{0,8}\s',re.IGNORECASE):"Transfer Debit - "},
   
    'cardtransactions':{re.compile(r'^[\d\s:*.,/-]*(HUF|EUR)[\w\s.]+(HUF|HU|EUR)[\s\w.-]*\n',re.IGNORECASE):"",
                        re.compile(r'\s([\dA-Za-z]{7,8})\s+(\d{3,})$',re.IGNORECASE):"",
                        re.compile(r'[\'\"]',re.IGNORECASE):""}}
    
    # mapping will tell which replacements need to be applied
    replacement_map = {
    "FEE, INTEREST": "fees",
    "TRANSFER": "transfers",
    "INCOME": "income",
    "OTHER DEBIT": "otherdebit",
    "OTHER CREDIT":"income",
    "CARD TRANSACTION": "cardtransactions"
    }
    
    # applying the replacements
    for k in smaller_dfs.keys():
      if k in replacement_map:
         smaller_dfs[k].loc[:, "DESCRIPTION"] = (smaller_dfs[k]["DESCRIPTION"]
                                                 .replace(replacements[replacement_map[k]], regex=True)
                                                 .fillna(value=k if k == "FEE, INTEREST" else smaller_dfs[k]["DESCRIPTION"]))

    return pd.concat([df for df in smaller_dfs.values()])

def bank2_process(bank2file):
  
  # Parsing the xml file
  tree = ET.parse(bank2file)
  root = tree.getroot()
  i=1

  header=[]
  data=[]

  for rw in root.find('{urn:schemas-microsoft-com:office:spreadsheet}Worksheet').iter('{urn:schemas-microsoft-com:office:spreadsheet}Row'):
    srs=[]
    for cl in rw.iter('{urn:schemas-microsoft-com:office:spreadsheet}Data'):
      if i==1:
        header.append(cl.text)
      else:
        srs.append(cl.text)

    data.append(srs)
    i+=1

  df=pd.DataFrame(data,columns=header).iloc[1:]

  

  return data_cleaning_bank2(df)

def data_cleaning_bank2(df):
    
    
    def classify_transaction(beneficiary, transactiontype, client, comment):
        # this function is for creating a description field for the dataframe
        # the information that i need for the classification can come from several fields
        transactiontype_map={
           "Jóváírás: Csop átutalás":"Salary - " + str(client),
           "AFR Jóváírás":"Transfer Debit - " + str(client) + " - " + str(comment),
           "POS bankkártya":str(client),
           "készpénzfelvétel":str(transactiontype),
           "betét lekötés":str(transactiontype),
           "AFR terhelés":"Transfer Credit - " + str(beneficiary) + " - " + str(comment)
        }

        for k in transactiontype_map:
           if k in transactiontype:
              return transactiontype_map[k]

        return   str(transactiontype) if  beneficiary is None else beneficiary


    df["DESCRIPTION"] = df.apply(lambda row: classify_transaction(row['BENEFICIARY'],
                                                           row['TYPE OF TRANSACTION'],
                                                           row['CLIENT NAME'],
                                                          row['COMMENT']), axis=1)

    # logic for replacements are the same as for the bank1 file, but here i dont need that many categories
    replacement_map = ["Bankkártyás vásárlás","POS","Kártyafoglalás"]

    replacements={
       re.compile(r"\s{2,}",re.IGNORECASE):" ",
       re.compile(r"\s\d{3,}\s.+\w{2}$",re.IGNORECASE):"",
       re.compile(r"\s\d{3,}",re.IGNORECASE):"",
       re.compile(r"\.SZ\.",re.IGNORECASE):"",
       re.compile(r"\s+\d+$",re.IGNORECASE):"",
       re.compile(r"^[\s\w]+\*",re.IGNORECASE):"",
       re.compile(r"[':]",re.IGNORECASE):""
    }

    transactiongroups=df.groupby("TYPE OF TRANSACTION")
    smaller_dfs={key:transactiongroups.get_group(key) for key in transactiongroups.groups}

    # applying replacements in DESCRIPTION field
    for k in smaller_dfs.keys():
       if any(item in k for item in replacement_map):
          smaller_dfs[k].loc[:, "DESCRIPTION"] = (smaller_dfs[k]["DESCRIPTION"].replace(replacements, regex=True))
          
    df=pd.concat([df for df in smaller_dfs.values()])

    # setting category ids and owner
    df[['CATEGORY ID', 'SUBCATEGORY ID',"OWNER"]]=["","","PersonY"]
  
    return df[["OWNER",'DATE', 'CATEGORY ID', 'SUBCATEGORY ID', 'DESCRIPTION', 'AMOUNT']]
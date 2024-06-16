
import pandas as pd
import xml.etree.ElementTree as ET
pd.options.mode.chained_assignment = None

def bank1_process(bank1file):

  df=pd.read_excel(bank1file,skiprows=9)


  df_dij=df.loc[df["TYPE OF TRANSACTION"]=="DÍJ, KAMAT"]
  df_utalas=df.loc[df["TYPE OF TRANSACTION"]=="ÁTUTALÁS"]
  df_jovedelem=df.loc[(df["TYPE OF TRANSACTION"]=="JÖVEDELEM")|(df["TYPE OF TRANSACTION"]=="EGYÉB JÓVÁÍRÁS")]
  df_egyeb=df.loc[df["TYPE OF TRANSACTION"]=="EGYÉB TERHELÉS"]
  df_kartya=df.loc[df["TYPE OF TRANSACTION"]=="KÁRTYATRANZAKCIÓ"]

  df_dij=data_cleaning_bank1(df_dij) if len(df_dij)!=0 else df_dij
  df_utalas=data_cleaning_bank1(df_utalas) if len(df_utalas)!=0 else df_utalas
  df_jovedelem=data_cleaning_bank1(df_jovedelem) if len(df_jovedelem)!=0 else df_jovedelem
  df_egyeb= data_cleaning_bank1(df_egyeb) if len(df_egyeb)!=0 else df_egyeb
  df_kartya=data_cleaning_bank1(df_kartya) if len(df_kartya)!=0 else df_kartya

  df=pd.concat([df_dij,df_utalas,df_jovedelem,df_egyeb,df_kartya])

  df[['CATEGORY ID', 'SUBCATEGORY ID',"OWNER"]]=["","","PersonX"]
  
  df=df[["OWNER","DATE",'CATEGORY ID', 'SUBCATEGORY ID','DESCRIPTION','AMOUNT']]
        
  
  return df


def data_cleaning_bank1(df):
    
    match df["TYPE OF TRANSACTION"].iloc[0]:
      case "DÍJ, KAMAT":

        return (df.replace({"DESCRIPTION":r'^[\w\s\\,-]+$'},{"DESCRIPTION":"UTALÁSI DÍJ"},regex=True)
                    .fillna(value={"DESCRIPTION":"DÍJ, KAMAT"}))

      case "ÁTUTALÁS":

        return (df.replace({"DESCRIPTION":r'^[\d\s-]*'},{"DESCRIPTION":"Utalás - "},regex=True)
                  .replace({"DESCRIPTION":r'\s'},{"DESCRIPTION":" "},regex=True))

      case "JÖVEDELEM"|"EGYÉB JÓVÁÍRÁS":

        return (df.replace({"DESCRIPTION":r'^[\d\s\-]*'},{"DESCRIPTION":"Munkabér - "},regex=True)
                  .replace({"DESCRIPTION":r'Partnerek\sközti\segyedi\sazonosító:\s\w+$'},{"DESCRIPTION":""},regex=True)
                  .replace({"DESCRIPTION":r'\sKözlemény[\w\s:-]+$'},{"DESCRIPTION":""},regex=True))

      case "EGYÉB TERHELÉS":

        return (df.replace({"DESCRIPTION":r'^[\w\s:,/-]*Noszlopy Társasház[\w\s:,/-]*$'},{"DESCRIPTION":"KÖZÖS KÖLTSÉG"},regex=True)
                    .replace({"DESCRIPTION":r'&&TF01'},{"DESCRIPTION":"HITEL"},regex=True)
                    .replace({"DESCRIPTION":r'^\d{8}-\d{8}-*\d{0,8}\s'},{"DESCRIPTION":"Utalás - "},regex=True))

      case "KÁRTYATRANZAKCIÓ":
        
          return (df.replace({"DESCRIPTION":r'^[\d\s:*.,/-]*(HUF|EUR)[\w\s.]+(HUF|HU|EUR)[\s\w.-]*\n'},{"DESCRIPTION":""},regex=True)
                    .replace({"DESCRIPTION":r'\s([\dA-Za-z]{7,8})\s+(\d{3,})$'},{"DESCRIPTION":""},regex=True)
                    .replace({"DESCRIPTION":r'[\'\"]'},{"DESCRIPTION":""},regex=True))

def bank2_process(bank2file):
  
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
    
    df = df[['AMOUNT', 'DATE', 'TYPE OF TRANSACTION', 'CLIENT NAME', 'BENEFICIARY', 'COMMENT']]
    
    def classify_transaction(kedvezményezett, tranzakció_típus, megbízó, közlemény):
        if kedvezményezett is None:
            if "Jóváírás: Csop átutalás" in tranzakció_típus:
                return "Munkabér - " + str(megbízó)
            elif "AFR Jóváírás" in tranzakció_típus:
                return "Beérkező utalás - " + str(megbízó) + " - " + str(közlemény)
            elif "POS bankkártya" in tranzakció_típus:
                return str(megbízó)
            else:
                return str(tranzakció_típus)
        else:
            if any(item in tranzakció_típus for item in ["készpénzfelvétel","betét lekötés"]):
                return str(tranzakció_típus)
            elif "AFR terhelés" in tranzakció_típus:
                return "Utalás - " + str(kedvezményezett) + " - " + str(közlemény)
            else:
                return kedvezményezett


    df["DESCRIPTION"] = df.apply(lambda row: classify_transaction(row['BENEFICIARY'],
                                                           row['TYPE OF TRANSACTION'],
                                                           row['CLIENT NAME'],
                                                          row['COMMENT']), axis=1)

    df_kartyatranzakcio=(df[df['TYPE OF TRANSACTION'].str.contains("Bankkártyás vásárlás|POS|Kártyafoglalás")]
                          .replace({"DESCRIPTION":r"\s{2,}"},{"DESCRIPTION":" "},regex=True) 
                          .replace({"DESCRIPTION":r"\s\d{3,}\s.+\w{2}$"},{"DESCRIPTION":""},regex=True) 
                          .replace({"DESCRIPTION":r"\s\d{3,}"},{"DESCRIPTION":""},regex=True)
                          .replace({"DESCRIPTION":r"\.SZ\."},{"DESCRIPTION":""},regex=True)
                          .replace({"DESCRIPTION":r"\s+\d+$"},{"DESCRIPTION":""},regex=True)
                          .replace({"DESCRIPTION":r"^[\s\w]+\*"},{"DESCRIPTION":""},regex=True)
                          .replace({"DESCRIPTION":r"[':]"},{"DESCRIPTION":""},regex=True)
                          
                          )

    df=pd.concat([df[~df['TYPE OF TRANSACTION'].str.contains("Bankkártyás vásárlás|POS|Kártyafoglalás")],df_kartyatranzakcio])

    df[['CATEGORY ID', 'SUBCATEGORY ID',"OWNER"]]=["","","PersonY"]
    
    
    return df[["OWNER",'DATE', 'CATEGORY ID', 'SUBCATEGORY ID', 'DESCRIPTION', 'AMOUNT']]
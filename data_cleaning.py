
import pandas as pd
import xml.etree.ElementTree as ET
pd.options.mode.chained_assignment = None



def cib_process(cibfile):

  df=pd.read_excel(cibfile,skiprows=9)


  df_dij=df.loc[df["TRANZAKCIÓTÍPUS"]=="DÍJ, KAMAT"]
  df_utalas=df.loc[df["TRANZAKCIÓTÍPUS"]=="ÁTUTALÁS"]
  
  df_jovedelem=df.loc[(df["TRANZAKCIÓTÍPUS"]=="JÖVEDELEM")|(df["TRANZAKCIÓTÍPUS"]=="EGYÉB JÓVÁÍRÁS")]
  
 
  df_egyeb=df.loc[df["TRANZAKCIÓTÍPUS"]=="EGYÉB TERHELÉS"]
  df_kartya=df.loc[df["TRANZAKCIÓTÍPUS"]=="KÁRTYATRANZAKCIÓ"]

  df_dij=data_cleaning_cib(df_dij) if len(df_dij)!=0 else df_dij
  df_utalas=data_cleaning_cib(df_utalas) if len(df_utalas)!=0 else df_utalas
  df_jovedelem=data_cleaning_cib(df_jovedelem) if len(df_jovedelem)!=0 else df_jovedelem
  df_egyeb= data_cleaning_cib(df_egyeb) if len(df_egyeb)!=0 else df_egyeb
  df_kartya=data_cleaning_cib(df_kartya) if len(df_kartya)!=0 else df_kartya

  df=pd.concat([df_dij,df_utalas,df_jovedelem,df_egyeb,df_kartya])

  
  df[['Kategória ID', 'Alkategória ID',"Tulajdonos"]]=["","","Eddie"]
  
  df=(df[["Tulajdonos","DÁTUM",'Kategória ID', 'Alkategória ID','KÖZLEMÉNY','ÖSSZEG']]
        .rename(columns={"KÖZLEMÉNY":"Leírás","ÖSSZEG":"Összeg"}))
  
  return df


def data_cleaning_cib(df):
    
    match df["TRANZAKCIÓTÍPUS"].iloc[0]:
      case "DÍJ, KAMAT":

        return (df.replace({"KÖZLEMÉNY":r'^[\w\s\\,-]+$'},{"KÖZLEMÉNY":"UTALÁSI DÍJ"},regex=True)
                    .fillna(value={"KÖZLEMÉNY":"DÍJ, KAMAT"}))

      case "ÁTUTALÁS":

        return (df.replace({"KÖZLEMÉNY":r'^[\d\s-]*'},{"KÖZLEMÉNY":"Utalás - "},regex=True)
                  .replace({"KÖZLEMÉNY":r'\s'},{"KÖZLEMÉNY":" "},regex=True))

      case "JÖVEDELEM"|"EGYÉB JÓVÁÍRÁS":

        return (df.replace({"KÖZLEMÉNY":r'^[\d\s\-]*'},{"KÖZLEMÉNY":"Munkabér - "},regex=True)
                  .replace({"KÖZLEMÉNY":r'Partnerek\sközti\segyedi\sazonosító:\s\w+$'},{"KÖZLEMÉNY":""},regex=True)
                  .replace({"KÖZLEMÉNY":r'\sKözlemény[\w\s:-]+$'},{"KÖZLEMÉNY":""},regex=True))

      case "EGYÉB TERHELÉS":

        return (df.replace({"KÖZLEMÉNY":r'^[\w\s:,/-]*Noszlopy Társasház[\w\s:,/-]*$'},{"KÖZLEMÉNY":"KÖZÖS KÖLTSÉG"},regex=True)
                    .replace({"KÖZLEMÉNY":r'&&TF01'},{"KÖZLEMÉNY":"HITEL"},regex=True)
                    .replace({"KÖZLEMÉNY":r'^\d{8}-\d{8}-*\d{0,8}\s'},{"KÖZLEMÉNY":"Utalás - "},regex=True))

      case "KÁRTYATRANZAKCIÓ":
        
          return (df.replace({"KÖZLEMÉNY":r'^[\d\s:*.,/-]*(HUF|EUR)[\w\s.]+(HUF|HU|EUR)[\s\w.-]*\n'},{"KÖZLEMÉNY":""},regex=True)
                    .replace({"KÖZLEMÉNY":r'\s([\dA-Za-z]{7,8})\s+(\d{3,})$'},{"KÖZLEMÉNY":""},regex=True)
                    .replace({"KÖZLEMÉNY":r'[\'\"]'},{"KÖZLEMÉNY":""},regex=True))

def granit_process(granitfile):
  
  tree = ET.parse(granitfile)
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

  #df=df[['Tranzakció típusa','Megbízó neve','Kedvezményezett neve','Közlemény']].head(13)
  df = data_cleaning_granit(df)

  return df

def data_cleaning_granit(df):
    
    df = df[['Összeg', 'Értéknap', 'Tranzakció típusa', 'Megbízó neve', 'Kedvezményezett neve', 'Közlemény']]
    
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


    df["Leírás"] = df.apply(lambda row: classify_transaction(row['Kedvezményezett neve'],
                                                           row['Tranzakció típusa'],
                                                           row['Megbízó neve'],
                                                          row['Közlemény']), axis=1)

    df_kartyatranzakcio=(df[df['Tranzakció típusa'].str.contains("Bankkártyás vásárlás|POS|Kártyafoglalás")]
                          .replace({"Leírás":r"\s{2,}"},{"Leírás":" "},regex=True) 
                          .replace({"Leírás":r"\s\d{3,}\s.+\w{2}$"},{"Leírás":""},regex=True) 
                          .replace({"Leírás":r"\s\d{3,}"},{"Leírás":""},regex=True)
                          .replace({"Leírás":r"\.SZ\."},{"Leírás":""},regex=True)
                          .replace({"Leírás":r"\s+\d+$"},{"Leírás":""},regex=True)
                          .replace({"Leírás":r"^[\s\w]+\*"},{"Leírás":""},regex=True)
                          .replace({"Leírás":r"[':]"},{"Leírás":""},regex=True)
                          
                          )

    df=pd.concat([df[~df['Tranzakció típusa'].str.contains("Bankkártyás vásárlás|POS|Kártyafoglalás")],df_kartyatranzakcio])

    df[['Kategória ID', 'Alkategória ID',"Tulajdonos"]]=["","","Anett"]
    
    
    df=(df[["Tulajdonos",'Értéknap', 'Kategória ID', 'Alkategória ID', 'Leírás', 'Összeg']]
          .rename(columns={"Értéknap":"DÁTUM"}))

    return df
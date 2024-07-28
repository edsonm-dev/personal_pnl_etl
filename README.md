# Revenue ETL

## About the Project

Purpose: Automating the process of cleaning banking transaction data, categorizing the costs and incomes and loading the transformed records to google sheets. The result is sourced by PowerBI for further analysis.

 - Sources: 
    - Account statement files (xls and xml) with transactions from two banks - monthly, API is not available
    - Categorization reference dataset from google sheets file for categorizing the transactions
    - Service account json file for authentication in google (not in the repository for natural reasons)

All data in the repository (amount, descriptions, partners, account numbers, dates) has been changed and/or randomized for privacy reasons.

### Built With

- Python libraries:
  - pandas
  - xml.etree
  - gspread, gspread_dataframe
  - re

## Usage

1. The user downloads the files from the banks
2. The python script (run by typing "python main.py" in CLI) parses the xml and xls files with Xml.etree and Pandas libraries. 
3. The description of the transactions are transformed to a more readable form with Regex.
4. The transactions are categorized with the help of the reference dataset from google sheets. 
5. The cleaned, categorized transactions are appended to the google sheets file with Gspread library. 
6. Finally the user can add and modify categorization if needed, otherwise the PowerBI dashboard can be refreshed for analyzing the transactions.

import streamlit as st
import numpy as np
import pandas as pd
import os

def main():
    st.sidebar.title("NLV Generation")
    app_mode = st.sidebar.selectbox("Choose the app mode",
                                    ["Upload data"])

    if app_mode == "Upload data":
        upload_data()
        st.markdown('**Once done with uploading files, click on Generate NLV**')
        if st.button('Generate NLV'):
            compute_NLV()
    
    return None

def upload_data():
    global EDF_file, EDF_file_yest, EDF_clearisk, EDF_clearisk_yest, volume_data
    EDF_file = st.file_uploader('CLR EDF Data for today')
    if EDF_file is not None:
        EDF_clearisk = pd.read_excel(EDF_file, sheet_name = "Clearisk")
        EDF_clearisk = EDF_clearisk[["Date", "Client", "Currency", "Clearisk Net Liquid Value (A)",
                                    "Clearisk Market Fee (B)", "Clearisk Clr Comms (C)"]]
        EDF_clearisk.dropna(inplace=True)
        if st.checkbox('Show data for today'):
            st.write(EDF_clearisk)
    
    EDF_file_yest = st.file_uploader('CLR EDF Data for previous day')
    if EDF_file_yest is not None:
        EDF_clearisk_yest = pd.read_excel(EDF_file_yest, sheet_name = "Clearisk")
        EDF_clearisk_yest = EDF_clearisk_yest[["Date", "Client", "Currency", "Clearisk Net Liquid Value (A)",
                                    "Clearisk Market Fee (B)", "Clearisk Clr Comms (C)"]]
        EDF_clearisk_yest.dropna(inplace=True)
        if st.checkbox('Show data for yesterday'):
            st.write(EDF_clearisk_yest)
    
    volume_file = st.file_uploader('Etrade daily volume report for today')
    if volume_file is not None:
        volume_data = pd.read_csv(volume_file, skiprows=1, header=None)
        volume_data.dropna(inplace=True)
        if st.checkbox('Show volume data'):
            st.write(volume_data)

    
def compute_NLV():
    currency_spot_today = pd.read_excel(EDF_file, sheet_name = "Control Account", nrows= 6)
    currency_spot_today = currency_spot_today[["Currency Code", "Spot Rate"]]
    currency_spot_today.set_index("Currency Code", inplace =True) 
    st.write(currency_spot_today)

    currency_spot_yest = pd.read_excel(EDF_file_yest, sheet_name = "Control Account", nrows= 6)
    currency_spot_yest = currency_spot_yest[["Currency Code", "Spot Rate"]]
    currency_spot_yest.set_index("Currency Code", inplace =True) 
    st.write(currency_spot_yest)

    EDF_clearisk["Spot Rate"] = EDF_clearisk["Currency"].apply(lambda x: currency_spot_today.loc[x, 'Spot Rate'])
    EDF_clearisk["Clearisk(USD)"] = EDF_clearisk["Clearisk Net Liquid Value (A)"]/ EDF_clearisk["Spot Rate"]
    EDF_clearisk["Commision"] = (EDF_clearisk["Clearisk Market Fee (B)"] + EDF_clearisk["Clearisk Clr Comms (C)"])/ EDF_clearisk["Spot Rate"] 
    st.write(EDF_clearisk)

    EDF_clearisk_yest["Spot Rate"] = EDF_clearisk_yest["Currency"].apply(lambda x: currency_spot_yest.loc[x, 'Spot Rate'])
    EDF_clearisk_yest["Clearisk(USD)"] = EDF_clearisk_yest["Clearisk Net Liquid Value (A)"]/ EDF_clearisk_yest["Spot Rate"]
    EDF_clearisk_yest["Commision"] = (EDF_clearisk_yest["Clearisk Market Fee (B)"] + EDF_clearisk_yest["Clearisk Clr Comms (C)"])/ EDF_clearisk_yest["Spot Rate"] 
    st.write(EDF_clearisk_yest)







    


if __name__ == "__main__":
    main()


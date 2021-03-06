import streamlit as st
import numpy as np
import pandas as pd
import os
import copy

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
        volume_data.drop_duplicates(inplace=True)
        volume_data.columns = ["Duplicate","Client", "Volume"]
        volume_data.drop(columns =  ["Duplicate"], inplace=True)
        volume_data.dropna(inplace=True)
        if st.checkbox('Show volume data'):
            st.write(volume_data)

    
def compute_NLV():
    col1, col2 = st.beta_columns(2)
    currency_spot_today = pd.read_excel(EDF_file, sheet_name = "Control Account", nrows= 6)
    currency_spot_today = currency_spot_today[["Currency Code", "Spot Rate"]]
    currency_spot_today.set_index("Currency Code", inplace =True)
    col1.write('Today') 
    col1.write(currency_spot_today)

    currency_spot_yest = pd.read_excel(EDF_file_yest, sheet_name = "Control Account", nrows= 6)
    currency_spot_yest = currency_spot_yest[["Currency Code", "Spot Rate"]]
    currency_spot_yest.set_index("Currency Code", inplace =True)
    col2.write('Previous day') 
    col2.write(currency_spot_yest)

    EDF_clearisk["Spot Rate"] = EDF_clearisk["Currency"].apply(lambda x: currency_spot_today.loc[x, 'Spot Rate'])
    EDF_clearisk["Clearisk(USD)"] = EDF_clearisk["Clearisk Net Liquid Value (A)"]/ EDF_clearisk["Spot Rate"]
    EDF_clearisk["Commission(USD)"] = (EDF_clearisk["Clearisk Market Fee (B)"] + EDF_clearisk["Clearisk Clr Comms (C)"])/ EDF_clearisk["Spot Rate"]
    st.write("**Today**") 
    st.write(EDF_clearisk)

    EDF_clearisk_yest["Spot Rate"] = EDF_clearisk_yest["Currency"].apply(lambda x: currency_spot_yest.loc[x, 'Spot Rate'])
    EDF_clearisk_yest["Clearisk(USD)"] = EDF_clearisk_yest["Clearisk Net Liquid Value (A)"]/ EDF_clearisk_yest["Spot Rate"]
    EDF_clearisk_yest["Commission(USD)"] = (EDF_clearisk_yest["Clearisk Market Fee (B)"] + EDF_clearisk_yest["Clearisk Clr Comms (C)"])/ EDF_clearisk_yest["Spot Rate"]
    st.write("**Previous day**")
    st.write(EDF_clearisk_yest)

    data_today = copy.deepcopy(EDF_clearisk)
    data_yest = copy.deepcopy(EDF_clearisk_yest)
    
    data_today = data_today[["Client", "Clearisk(USD)", "Commission(USD)"]]
    data_yest = data_yest[["Client", "Clearisk(USD)", "Commission(USD)"]]
    data_today = data_today.groupby(["Client"], as_index=False).sum()
    data_yest = data_yest.groupby(["Client"], as_index=False).sum()
    st.write("**Today**")
    st.write(data_today)
    data_yest.rename(columns={"Clearisk(USD)": "Clearisk_T-1(USD)"})
    st.write("**Previous day**")
    st.write(data_yest)
    
    data_today["Change"] = data_today["Clearisk(USD)"] - data_yest["Clearisk(USD)"]
    data_today = data_today.merge(volume_data, on = "Client")
    #data_today = data_today.insert(2, "Clearisk_T-1(USD)", data_yest["Clearisk_T-1(USD)"])
    st.write("**NLV**")

    st.write(data_today)

    

if __name__ == "__main__":
    main()




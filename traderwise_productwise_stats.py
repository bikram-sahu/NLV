import streamlit as st
import numpy as np
import pandas as pd
import os
import copy

def main():
    st.sidebar.title("Traderwise-Productwise Statistics")
    app_mode = st.sidebar.selectbox("Choose the app mode",
                                    ["Analytics"])

    if app_mode == "Analytics":
        upload_data()
        analytics_by = st.sidebar.selectbox("Select", ["by Client", "by Contract Group"])
        run_analytics(analytics_by)
    

def upload_data():
    global qtr_data, volume_data
    productwise_data = st.file_uploader('Upload productwise data')
    if productwise_data is not None:
        qtr_data = pd.read_excel(productwise_data, sheet_name = "Gross PNL By Product")
        qtr_data.drop(columns = ["Contract Type", "Base Currency", "AUD", "CAD", "CHF", "EUR", "GBP", "HKD", "JPY", "NOK", "SEK", "USD"], inplace=True)
        #qtr_data = qtr_data[["Client", "Contract Code", "Total"]]
        #qtr_data.dropna(inplace=True)
        qtr_data.drop(np.linspace(0, 142, 143), inplace=True)
        if st.checkbox('Show data for today'):
            st.write(qtr_data)

    volume_file = st.file_uploader('Etrade daily volume report for today')
    if volume_file is not None:
        volume_data = pd.read_csv(volume_file, skiprows=1, header=None)
        volume_data.drop_duplicates(inplace=True)
        volume_data.columns = ["Duplicate","Client", "Volume"]
        volume_data.drop(columns =  ["Duplicate"], inplace=True)
        volume_data.dropna(inplace=True)
        if st.checkbox('Show volume data'):
            st.write(volume_data)

def run_analytics(analytics_by):
    if analytics_by == "by Client":
        st.write(qtr_data.groupby(['Client']).sum())
        by_client = qtr_data.groupby(['Client'])
        st.bar_chart(by_client.sum()["Total"])
        st.markdown("**Traderwise Stats**")
        client_num = st.text_input("Enter Client number", "EE000")
        #st.write(by_client.get_group(client_num))
        per_client = by_client.get_group(client_num)
        st.write(per_client.groupby(["Contract Group"]).sum())



    if analytics_by == "by Contract Group":
        st.write(qtr_data.groupby(['Contract Group']).sum())
        by_contract = qtr_data.groupby(['Contract Group']).sum()
        st.bar_chart(by_contract["Total"])




    





if __name__ == "__main__":
    main()
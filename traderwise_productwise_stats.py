import streamlit as st
import numpy as np
import pandas as pd
import os
import copy

def main():
    st.sidebar.title("Month to Date Productwise Statistics")
    app_mode = st.sidebar.selectbox("Mode",
                                    ["Analytics"])

    if app_mode == "Analytics":
        #upload_data()
        load_data()
        analytics_by = st.sidebar.selectbox("Select", ["by Client", "Overall Stats"])
        run_analytics(analytics_by)
    

def upload_data():
    global qtr_data, volume_data
    productwise_data = st.file_uploader('Upload productwise data')
    if productwise_data is not None:
        qtr_data = pd.read_excel(productwise_data, sheet_name = "Gross PNL By Product")
        qtr_data.drop(columns = ["Contract Type", "Base Currency", "AUD", "CAD", "CHF", "EUR", "GBP", "HKD", "JPY", "NOK", "SEK", "USD"], inplace=True)
        #qtr_data.dropna(inplace=True)
        if st.checkbox('Show data for today'):
            st.write(qtr_data)

    volume_file = st.file_uploader('Volume data')
    if volume_file is not None:
        volume_data = pd.read_csv(volume_file, skiprows=1, header=None)
        volume_data.drop_duplicates(inplace=True)
        volume_data.columns = ["Duplicate","Client", "Volume"]
        volume_data.drop(columns =  ["Duplicate"], inplace=True)
        volume_data.dropna(inplace=True)
        if st.checkbox('Show volume data'):
            st.write(volume_data)

def load_data():
    st.date_input('Date input (currently this is not linked)')
    global qtr_data, volume_data, transaction_data
    productwise_data = "Gross PNL By Product (20).xlsx"
    transaction_data_file = "Transactions Jan-21.xlsx"
    qtr_data = pd.read_excel(productwise_data, sheet_name = "Gross PNL By Product")
    qtr_data = qtr_data[qtr_data['Client'].map(len) <= 5]
    qtr_data.drop(columns = ["Contract Type", "Base Currency", "AUD", "CAD", "CHF", "EUR", "GBP", "HKD", "JPY", "NOK", "SEK", "USD"], inplace=True)
    if st.checkbox('Show data'):
        st.write(qtr_data)
    transaction_data = pd.read_excel(transaction_data_file, sheet_name="Sheet2", skiprows = 1)
    transaction_data.drop([len(transaction_data)-1], inplace=True)
    transaction_data.drop(columns = ["Grand Total"], inplace=True)
    transaction_data.set_index("Row Labels", inplace=True)
    #st.write(transaction_data)
    

    

def run_analytics(analytics_by):
    if analytics_by == "by Client":
        
        by_client = qtr_data.groupby(['Client'], as_index=False)
        #st.write(type(by_client))
        st.write(qtr_data.groupby(['Client'], as_index=False).sum())
        #st.bar_chart(by_client.sum()["Total"])

        with open("mumbai_traders.txt") as file:
            mumbai_traders_list = [line.strip() for line in file]
        #by_client[by_client["Client"] =]
        
        st.markdown("**Traderwise Stats**")
        #client_num = st.selectbox("Select a Client Id", qtr_data['Client'].unique())
        client_num = st.selectbox("Select a Client Id", mumbai_traders_list)
        per_client = by_client.get_group(client_num)
        
        #col1, col2 = st.beta_columns((2,1))
        #col1.write(per_client.groupby(["Contract Group", "Contract Sub Group", "Contract Code"], as_index=False).sum())
        #col2.write(transaction_data.loc[client_num].dropna().div(2))
        #st.write(type(per_client.groupby(["Contract Group", "Contract Sub Group", "Contract Code"]).sum()))
        #st.write(type(transaction_data.loc[client_num].dropna().div(2)))
        df1 = per_client.groupby(["Contract Group", "Contract Sub Group", "Contract Code"], as_index=False).sum()
        df2 = transaction_data.loc[client_num].fillna(0).div(2)

        df1["RT"] = df1["Contract Code"].apply(lambda x: df2.loc[x])
        #st.markdown("**TEST**")
        st.write(df1)
        

    if analytics_by == "Overall Stats":
        st.write(qtr_data.groupby(['Contract Group']).sum())
        by_contract = qtr_data.groupby(['Contract Group']).sum() 
        st.bar_chart(by_contract["Total"])


if __name__ == "__main__":
    main()
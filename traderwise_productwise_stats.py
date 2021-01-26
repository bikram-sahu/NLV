import streamlit as st
import numpy as np
import pandas as pd
import os
import copy

import dropbox

token = "ogCBN3Of8vMAAAAAAAAAAeokgvH2eZ1cGgVSQDOqLNFkOYKqykgroZ8O9jfc_mMi"
dbx = dropbox.Dropbox(token)


# Security
#passlib,hashlib,bcrypt,scrypt
import hashlib
def make_hashes(password):
	return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password,hashed_text):
	if make_hashes(password) == hashed_text:
		return hashed_text
	return False
# DB Management
import sqlite3 
conn = sqlite3.connect('data.db')
c = conn.cursor()
# DB  Functions
def create_usertable():
	c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT,password TEXT)')


def add_userdata(username,password):
	c.execute('INSERT INTO userstable(username,password) VALUES (?,?)',(username,password))
	conn.commit()

def login_user(username,password):
	c.execute('SELECT * FROM userstable WHERE username =? AND password = ?',(username,password))
	data = c.fetchall()
	return data


def view_all_users():
	c.execute('SELECT * FROM userstable')
	data = c.fetchall()
	return data


def main():
    st.title("Month to Date Productwise Statistics")
    app_mode = st.sidebar.selectbox("Mode",
                                    ["Login"])

    if app_mode == "Login":
        #st.subheader("Login Section")
        username = st.sidebar.text_input("User Name")
        password = st.sidebar.text_input("Password", type='password')
        if st.sidebar.checkbox("Login"):
            create_usertable()
            hashed_pswd = make_hashes(password)
            result = login_user(username,check_hashes(password,hashed_pswd))
            if result:
                st.sidebar.success("Logged In as {}".format(username))
                #upload_data()
                load_data()
                analytics_by = st.sidebar.selectbox("Select", ["by Client", "Overall Stats"])
                run_analytics(analytics_by)
            else:
                st.warning("Incorrect Username/Password")


def load_data():
    #st.date_input('Date input (currently this is not linked)')
    global qtr_data, volume_data, transaction_data
    productwise_data = "/Gross PNL By Product (20).xlsx"
    transaction_data_file = "/Transactions Jan-21.xlsx"
    _, f = dbx.files_download(productwise_data)
    f = f.content

    qtr_data = pd.read_excel(f, sheet_name = "Gross PNL By Product")
    qtr_data = qtr_data[qtr_data['Client'].map(len) <= 5]
    qtr_data.drop(columns = ["Contract Type", "Base Currency", "AUD", "CAD", "CHF", "EUR", "GBP", "HKD", "JPY", "NOK", "SEK", "USD"], inplace=True)
    #if st.checkbox('Show data'):
    #    st.write(qtr_data)
    _, f = dbx.files_download(transaction_data_file)
    f = f.content
    transaction_data = pd.read_excel(f, sheet_name="Sheet2", skiprows = 1)
    transaction_data.drop([len(transaction_data)-1], inplace=True)
    transaction_data.drop(columns = ["Grand Total"], inplace=True)
    transaction_data.set_index("Row Labels", inplace=True)
    #st.write(transaction_data)
    

    

def run_analytics(analytics_by):
    if analytics_by == "by Client":
        
        by_client = qtr_data.groupby(['Client'], as_index=False)
        #st.write(type(by_client))
        #st.write(qtr_data.groupby(['Client'], as_index=False).sum())
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
import streamlit as st
import numpy as np
import pandas as pd
import os
import copy

from st_aggrid import AgGrid
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode

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
    st.sidebar.title("Month to Date Productwise Statistics")
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
                productwise_data = "/MTDPL.xlsx"
                transaction_data_file = "/Transactions Jan-21.xlsx"
                MIS_file_name = "/MIS Mumbai.xlsx"
                MIS_data = load_MIS_data(MIS_file_name)
                qtr_data, transaction_data = load_data(productwise_data, transaction_data_file)
                analytics_by = st.sidebar.selectbox("Select", ["by Client", "Overall Stats", "MIS"])
                run_analytics(analytics_by, qtr_data, transaction_data, MIS_data)
            else:
                st.warning("Incorrect Username/Password")

@st.cache
def load_data(productwise_data, transaction_data_file):
    #st.date_input('Date input (currently this is not linked)')
    global qtr_data, transaction_data

    _, f = dbx.files_download(productwise_data)
    f = f.content

    qtr_data = pd.read_excel(f, sheet_name = "Gross PNL By Product", engine='openpyxl')
    qtr_data = qtr_data[qtr_data['Client'].map(len) <= 5]
    qtr_data.drop(columns = ["Contract Type", "Base Currency", "AUD", "CAD", "CHF", "EUR", "GBP", "HKD", "JPY", "NOK", "SEK", "USD"], inplace=True)
    #if st.checkbox('Show data'):
    #    st.write(qtr_data)
    _, f = dbx.files_download(transaction_data_file)
    f = f.content
    transaction_data = pd.read_excel(f, sheet_name="Sheet2", engine='openpyxl', skiprows = 1)
    transaction_data.drop([len(transaction_data)-1], inplace=True)
    transaction_data.drop(columns = ["Grand Total"], inplace=True)
    transaction_data.set_index("Row Labels", inplace=True)
    #st.write(transaction_data)
    return qtr_data, transaction_data

@st.cache
def load_MIS_data(MIS_file_name):
    global MIS_data

    _, f = dbx.files_download(MIS_file_name)
    f = f.content

    MIS_data = pd.read_excel(f, sheet_name = "Stats", engine='openpyxl', skiprows=1, nrows= 54)
    MIS_data.drop(columns = ["Unnamed: 4", "Unnamed: 8", "Unnamed: 12"], inplace= True)
    return MIS_data

@st.cache
def color_negative_red(val):
    """
    Takes a scalar and returns a string with
    the css property `'color: red'` for negative
    strings, black otherwise.
    """
    color = 'red' if val < 0 else 'black'
    return 'color: %s' % color

    

def run_analytics(analytics_by, qtr_data, transaction_data, MIS_data):
    if analytics_by == "by Client":
        
        by_client = qtr_data.groupby(['Client'], as_index=False)
        #st.write(type(by_client))
        #st.write(qtr_data.groupby(['Client'], as_index=False).sum())
        #st.bar_chart(by_client.sum()["Total"])

        with open("mumbai_traders.txt") as file:
            mumbai_traders_list = [line.strip() for line in file]
        #by_client[by_client["Client"] =]
        
        st.markdown("**Traderwise Stats (Mumbai)**")
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
        st.write(df1)
        
        

    elif analytics_by == "Overall Stats":
        st.write(qtr_data.groupby(['Contract Group']).sum())
        by_contract = qtr_data.groupby(['Contract Group']).sum() 
        st.bar_chart(by_contract["Total"])

    elif analytics_by == "MIS":
        #MIS_data = MIS_data.style.applymap(color_negative_red)
        df = MIS_data.round(1)
        gb = GridOptionsBuilder.from_dataframe(df)
        cellsytle_jscode = JsCode("""
        function(params) {
            if (params.value <= 0.5) {
                return {
                    'color': 'white',
                    'backgroundColor': 'red'
                }
            } else {
                return {
                    'color': 'black',
                    'backgroundColor': 'white'
                }
            }
        };
        """)
        gb.configure_column("% of Up days", cellStyle=cellsytle_jscode)
        gb.configure_grid_options(domLayout='normal')
        gridOptions = gb.build()

        #Display the grid
        with st.spinner("Loading Grid..."):
            st.header("Streamlit Ag-Grid")
            grid_response = AgGrid(
                df, 
                gridOptions=gridOptions, 
                width='100%',
                allow_unsafe_jscode=True, #Set it to True to allow jsfunction to be injected
                )

        df = grid_response['data']
        selected = grid_response['selected_rows']
        selected_df = pd.DataFrame(selected)
        #AgGrid(df)

    



if __name__ == "__main__":
    main()
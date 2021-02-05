import streamlit as st
import numpy as np
import pandas as pd
import os
import copy



import dropbox

token = "VxZJ61zTijgAAAAAAAAAATiNeOOajjeNc47H1krHeuyNc9qpVA1g0htEGSHSIYXl"
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
	c.execute("""CREATE TABLE IF NOT EXISTS userstable (
        username TEXT,
        password TEXT
    )""")


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
                                    ["Login", "SignUp"])

    if app_mode == "Login":
        username = st.sidebar.text_input("User Name")
        password = st.sidebar.text_input("Password", type='password')
        if st.sidebar.checkbox("Login"):
            create_usertable()
            hashed_pswd = make_hashes(password)
            result = login_user(username,check_hashes(password,hashed_pswd))
            if result:
                st.markdown("### Last updated on: 04-Feb-2021")
                month_selected = st.sidebar.selectbox('Select a month', ["Feb 2021", "Jan 2021"])
                #st.sidebar.success("Logged In as {}".format(username))
                mtd_gross_pnl = "/" + month_selected + "/MTDPL.xlsx"
                transaction_data_file = "/" + month_selected + "/Transactions.xlsx"
                #st.sidebar.write("Gross PnL Data as of: " + "29-Jan-2021")
                #st.sidebar.write("RT data as of: " + "29-Jan-2021")
                qtr_data, transaction_data = load_data(mtd_gross_pnl, transaction_data_file)
                transaction_raw, instrument_name = load_transaction_data(transaction_data_file)

                analytics_by = st.sidebar.selectbox("Select the branch", ["Overall Stats", "Mumbai", "Kolkata"])
                run_analytics(analytics_by, qtr_data, transaction_data, transaction_raw, instrument_name)
            else:
                st.warning("Incorrect Username/Password")
                
    elif app_mode == "SignUp":
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_password = st.text_input("Password",type='password')
        
        if st.button("Signup"):
            create_usertable()
            add_userdata(new_user,make_hashes(new_password))
            st.success("You have successfully created a valid Account")
            st.info("Go to Login Menu to login")
    

@st.cache
def load_data(mtd_gross_pnl, transaction_data_file):
    global qtr_data, transaction_data

    _, f = dbx.files_download(mtd_gross_pnl)
    f = f.content

    qtr_data = pd.read_excel(f, sheet_name = "Gross PNL By Product", engine='openpyxl')
    qtr_data = qtr_data[qtr_data['Client'].map(len) <= 5]
    qtr_data.drop(columns = ["Contract Type", "Base Currency", "AUD", "CAD", "CHF", "EUR", "GBP", "HKD", "JPY", "NOK", "SEK", "USD"], inplace=True)
    _, f = dbx.files_download(transaction_data_file)
    f = f.content
    transaction_data = pd.read_excel(f, sheet_name="Sheet2", engine='openpyxl', skiprows = 1)
    transaction_data.drop([len(transaction_data)-1], inplace=True)
    transaction_data.drop(columns = ["Grand Total"], inplace=True)
    transaction_data.set_index("Row Labels", inplace=True)
    return qtr_data, transaction_data

@st.cache(allow_output_mutation=True)
def load_transaction_data(transaction_data_file):
    global transaction_raw

    _, f = dbx.files_download(transaction_data_file)
    f = f.content
    transaction_raw = pd.read_excel(f, sheet_name="Sheet3", engine='openpyxl')

    instrument_name = pd.read_excel(f, sheet_name="Sheet5", engine='openpyxl')
    #transaction_raw.drop([0, 85, 86], inplace=True)
    return transaction_raw, instrument_name



def color_negative_red(val):
    """
    Takes a scalar and returns a string with
    the css property `'color: red'` for negative
    strings, black otherwise.
    """
    color = 'red' if val < 0 else 'green'
    return 'color: %s' % color


def run_analytics(analytics_by, qtr_data, transaction_data, transaction_raw, instrument_name):
    if analytics_by == "Mumbai":
        #st.write(transaction_data)
        by_client = qtr_data.groupby(['Client'], as_index=False)
        

        with open("mumbai_traders.txt") as file:
            mumbai_traders = [line.strip() for line in file]

        
        st.markdown("**Traderwise Stats (Mumbai)**")
        all_traders = set(qtr_data.Client.unique())
        mumbai_traders_list = []
        for trader in mumbai_traders:
            if trader in all_traders:
                mumbai_traders_list.append(trader)


        client_num = st.selectbox("Select a Client Id", mumbai_traders_list)
        per_client = by_client.get_group(client_num)

        #df1 = per_client.groupby(["Contract Group", "Contract Sub Group", "Contract Code"], as_index=False).sum()
        df1 = per_client.groupby(["Contract Code"], as_index=False).sum()
        df2 = transaction_data.loc[client_num].fillna(0).div(2)
        df1["RT"] = df1["Contract Code"].apply(lambda x: df2.loc[x] if x in df2 else 0)

        mumbai = pd.DataFrame()
        for trader in mumbai_traders_list:
            df = by_client.get_group(trader)
            df11 = df.groupby(["Contract Code"], as_index=False).sum()
            df22 = transaction_data.loc[trader].fillna(0).div(2)
            df11["RT"] = df11["Contract Code"].apply(lambda x: df22.loc[x] if x in df22 else 0)
            result = pd.concat([mumbai, df11])
            mumbai = result

        contract_names = copy.deepcopy(transaction_raw)
        contract_names.drop(columns=["Sum of Qty"], inplace=True)
        contract_names = contract_names.rename(columns={"Instruments": "Contract Code"}, errors="raise") 

        sum_Total = df1["Total"].sum()
        sum_RT = df1["RT"].sum()
        df1 = df1.style.applymap(color_negative_red, subset=pd.IndexSlice[:, ['Total']])
        st.dataframe(df1.format({'RT': '{:.0f}', 'Total': '{:.0f}'}), height=2500)

        st.write("Total PnL: ", int(sum_Total))
        st.write("Total RT: ", int(sum_RT))

        st.markdown("**All Traders (Mumbai)**")
        mumbai = mumbai.groupby("Contract Code", as_index=False).sum()
        mumbai_final = pd.merge(contract_names,  
                      mumbai,  
                      on ='Contract Code')

        sum_Total = mumbai_final["Total"].sum()
        sum_RT = mumbai_final["RT"].sum()
        mumbai_final = mumbai_final.style.applymap(color_negative_red, subset=pd.IndexSlice[:, ['Total']])
        st.dataframe(mumbai_final.format({"RT": '{:.0f}', 'Total': '{:.0f}'}), height=2500)
        st.write("Total PnL: ", int(sum_Total))
        st.write("Total RT: ", int(sum_RT))


    if analytics_by == "Kolkata":
        #st.write(transaction_data)
        by_client = qtr_data.groupby(['Client'], as_index=False)
        

        with open("kolkata_traders.txt") as file:
            kolkata_traders = [line.strip() for line in file]

        
        st.markdown("**Traderwise Stats (Kolkata)**")
        all_traders = set(qtr_data.Client.unique())
        kolkata_traders_list = []
        for trader in kolkata_traders:
            if trader in all_traders:
                kolkata_traders_list.append(trader)


        client_num = st.selectbox("Select a Client Id", kolkata_traders_list)
        per_client = by_client.get_group(client_num)

        #df1 = per_client.groupby(["Contract Group", "Contract Sub Group", "Contract Code"], as_index=False).sum()
        df1 = per_client.groupby(["Contract Code"], as_index=False).sum()
        df2 = transaction_data.loc[client_num].fillna(0).div(2)
        df1["RT"] = df1["Contract Code"].apply(lambda x: df2.loc[x] if x in df2 else 0)

        kolkata = pd.DataFrame()
        for trader in kolkata_traders_list:
            df = by_client.get_group(trader)
            df11 = df.groupby(["Contract Code"], as_index=False).sum()
            df22 = transaction_data.loc[trader].fillna(0).div(2)
            df11["RT"] = df11["Contract Code"].apply(lambda x: df22.loc[x] if x in df22 else 0)
            result = pd.concat([kolkata, df11])
            kolkata = result

        contract_names = copy.deepcopy(transaction_raw)
        contract_names.drop(columns=["Sum of Qty"], inplace=True)
        contract_names = contract_names.rename(columns={"Instruments": "Contract Code"}, errors="raise") 

        sum_Total = df1["Total"].sum()
        sum_RT = df1["RT"].sum()
        df1 = df1.style.applymap(color_negative_red, subset=pd.IndexSlice[:, ['Total']])
        st.dataframe(df1.format({'RT': '{:.0f}', 'Total': '{:.0f}'}), height=2500)

        st.write("Total PnL: ", int(sum_Total))
        st.write("Total RT: ", int(sum_RT))

        st.markdown("**All Traders (kolkata)**")
        kolkata = kolkata.groupby("Contract Code", as_index=False).sum()
        kolkata_final = pd.merge(contract_names,  
                      kolkata,  
                      on ='Contract Code')

        sum_Total = kolkata_final["Total"].sum()
        sum_RT = kolkata_final["RT"].sum()
        kolkata_final = kolkata_final.style.applymap(color_negative_red, subset=pd.IndexSlice[:, ['Total']])
        st.dataframe(kolkata_final.format({"RT": '{:.0f}', 'Total': '{:.0f}'}), height=2500)
        st.write("Total PnL: ", int(sum_Total))
        st.write("Total RT: ", int(sum_RT))
        
        
        

    elif analytics_by == "Overall Stats":
        
        df = qtr_data.groupby(['Contract Group']).sum()
        by_contract_code = qtr_data.groupby(['Contract Code'], as_index=False).sum()
        by_contract_code.rename(columns = {"Contract Code": "Instruments"}, inplace=True)
        inner_join = pd.merge(transaction_raw,  
                      by_contract_code,  
                      on ='Instruments')
        
        sum_Total = inner_join["Total"].sum()
        st.write("MTD Total PnL:", int(sum_Total))
        st.write("MTD Sum of Qty:", int(inner_join["Sum of Qty"].sum()))

        inner_join = inner_join.style.applymap(color_negative_red, subset=pd.IndexSlice[:, ['Total']])
        st.dataframe(inner_join.format({'Sum of Qty': '{:.0f}', 'Total': '{:.0f}'}), height=2500)
    

if __name__ == "__main__":
    main()
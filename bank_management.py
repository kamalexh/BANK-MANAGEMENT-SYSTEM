import base64
import streamlit as st
import sqlite3
import random
import pandas as pd

# Function to create connection to SQLite database
def create_connection(db_file):
    """
    Establishes a connection to the SQLite database.

    Parameters:
        db_file (str): The path to the SQLite database file.

    Returns:
        conn: The SQLite database connection object.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        st.error(f"Error creating database connection: {e}")
    return conn

# Function to generate a unique 8-digit account number
def generate_account_number(conn):
    """
    Generates a unique 8-digit account number.

    Parameters:
        conn: The SQLite database connection object.

    Returns:
        int: A unique 8-digit account number.
    """
    while True:
        account_number = random.randint(10000000, 99999999)
        cursor = conn.cursor()
        cursor.execute('''SELECT account_number FROM accounts WHERE account_number = ?''', (account_number,))
        existing_account = cursor.fetchone()
        if not existing_account:
            return account_number

# Function to create account
def create_account(conn, name, age, gender):
    """
    Creates a new account with the provided details.

    Parameters:
        conn: The SQLite database connection object.
        name (str): The name of the account holder.
        age (int): The age of the account holder.
        gender (str): The gender of the account holder.

    Returns:
        int or None: The account number if account creation is successful, otherwise None.
    """
    try:
        account_number = generate_account_number(conn)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO accounts (account_number, name, age, gender, balance) VALUES (?, ?, ?, ?, ?)''', (account_number, name, age, gender, 0))
        conn.commit()
        st.success("Account created successfully!")
        return account_number
    except sqlite3.Error as e:
        st.error(f"Error creating account: {e}")
        return None

# Function to delete account
def delete_account(conn, account_number):
    """
    Deletes the account with the specified account number.

    Parameters:
        conn: The SQLite database connection object.
        account_number (int): The account number of the account to be deleted.
    """
    try:
        cursor = conn.cursor()
        cursor.execute('''DELETE FROM accounts WHERE account_number = ?''', (account_number,))
        conn.commit()
        st.success("Account deleted successfully!")
    except sqlite3.Error as e:
        st.error(f"Error deleting account: {e}")

# Function to deposit money
def deposit(conn, account_number, amount):
    """
    Deposits the specified amount into the account with the given account number.

    Parameters:
        conn: The SQLite database connection object.
        account_number (int): The account number of the account to deposit money into.
        amount (float): The amount of money to deposit.
    """
    try:
        cursor = conn.cursor()
        # Check if the account exists
        cursor.execute('''SELECT * FROM accounts WHERE account_number = ?''', (account_number,))
        account = cursor.fetchone()
        if account:
            cursor.execute('''UPDATE accounts SET balance = balance + ? WHERE account_number = ?''', (amount, account_number))
            cursor.execute('''INSERT INTO transactions (account_number, transaction_type, amount) VALUES (?, ?, ?)''', (account_number, 'Deposit', amount))
            conn.commit()
            st.success("Deposit successful!")
        else:
            st.error("Account does not exist!")
    except sqlite3.Error as e:
        st.error(f"Error depositing money: {e}")

# Function to withdraw money
def withdraw(conn, account_number, amount):
    """
    Withdraws the specified amount from the account with the given account number.

    Parameters:
        conn: The SQLite database connection object.
        account_number (int): The account number of the account to withdraw money from.
        amount (float): The amount of money to withdraw.
    """
    try:
        cursor = conn.cursor()
        # Check if the account exists
        cursor.execute('''SELECT balance FROM accounts WHERE account_number = ?''', (account_number,))
        balance = cursor.fetchone()
        if balance is not None:
            balance = balance[0]
            if balance >= amount:
                cursor.execute('''UPDATE accounts SET balance = balance - ? WHERE account_number = ?''', (amount, account_number))
                cursor.execute('''INSERT INTO transactions (account_number, transaction_type, amount) VALUES (?, ?, ?)''', (account_number, 'Withdraw', amount))
                conn.commit()
                st.success("Withdrawal successful!")
            else:
                st.error("Insufficient balance!")
        else:
            st.error("Account does not exist!")
    except sqlite3.Error as e:
        st.error(f"Error withdrawing money: {e}")

# Function to check balance
def check_balance(conn, account_number):
    """
    Retrieves and displays the balance of the account with the specified account number.

    Parameters:
        conn: The SQLite database connection object.
        account_number (int): The account number of the account to check balance for.
    """
    try:
        cursor = conn.cursor()
        cursor.execute('''SELECT name, age, gender, balance FROM accounts WHERE account_number = ?''', (account_number,))
        account_info = cursor.fetchone()
        if account_info:
            st.write(f"Name: {account_info[0]}")
            st.write(f"Age: {account_info[1]}")
            st.write(f"Gender: {account_info[2]}")
            st.write(f"Balance: {account_info[3]}")
        else:
            st.error("Account does not exist!")
    except sqlite3.Error as e:
        st.error(f"Error checking balance: {e}")

# Function to check transaction history
def transaction_history(conn, account_number):
    """
    Retrieves and displays the transaction history of the account with the specified account number.

    Parameters:
        conn: The SQLite database connection object.
        account_number (int): The account number of the account to check transaction history for.
    """
    try:
        cursor = conn.cursor()
        cursor.execute('''SELECT transaction_type, amount FROM transactions WHERE account_number = ?''', (account_number,))
        transactions = cursor.fetchall()
        if transactions:
            st.write("Transaction History:")
            for transaction in transactions:
                st.write(f"Type: {transaction[0]}, Amount: {transaction[1]}")
        else:
            st.error("No transaction history available!")
    except sqlite3.Error as e:
        st.error(f"Error fetching transaction history: {e}")

# Function to display all account details
def display_all_accounts(conn):
    """
    Retrieves and displays all account details.

    Parameters:
        conn: The SQLite database connection object.
    """
    try:
        cursor = conn.cursor()
        cursor.execute('''SELECT * FROM accounts''')
        accounts = cursor.fetchall()
        if accounts:
            st.write("All Accounts:")
            df = pd.DataFrame(accounts, columns=["Account Number", "Name", "Age", "Gender", "Balance"])
            # Add a serial number column starting from 1
            df.insert(0, 'Serial Number', range(1, len(df) + 1))
            st.write(df)
            # Download link for Excel file
            csv = df.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
            href = f'<a href="data:file/csv;base64,{b64}" download="all_accounts.csv">Download CSV File</a>'
            st.markdown(href, unsafe_allow_html=True)
        else:
            st.error("No accounts found!")
    except sqlite3.Error as e:
        st.error(f"Error fetching account details: {e}")

# Main function
def main():
    st.title("Bank Management System")
    
    # Display Welcome message
    st.write("Welcome to Bank Management System!")
    
    # Create a connection to the SQLite database
    conn = create_connection("bank.db")
    if conn is None:
        st.error("Error: Unable to create database connection.")
        return
    
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (account_number TEXT PRIMARY KEY, name TEXT, age INTEGER, gender TEXT, balance REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY, account_number TEXT, transaction_type TEXT, amount REAL)''')

    menu = ["Create Account", "Delete Account", "Deposit", "Withdraw", "Check Balance", "Transaction History", "View All Accounts"]
    selected_option = st.sidebar.radio("Menu", menu, index=None)

    # Display appropriate content based on the selected menu option
    if selected_option == "Create Account":
        st.subheader("Create Account")
        name = st.text_input("Enter Name")
        age = st.number_input("Enter Age", min_value=16, step=1)
        gender = st.selectbox("Select Gender", ["Male", "Female", "Other"])
        if st.button("Create"):
            account_number = create_account(conn, name, age, gender)
            if account_number:
                st.write(f"Account Number: {account_number}")
    elif selected_option == "Delete Account":
        st.subheader("Delete Account")
        account_number = st.text_input("Enter Account Number")
        if st.button("Delete"):
            delete_account(conn, account_number)
    elif selected_option == "Deposit":
        st.subheader("Deposit")
        account_number = st.text_input("Enter Account Number")
        amount = st.number_input("Enter Amount to Deposit")
        if st.button("Deposit"):
            deposit(conn, account_number, amount)
    elif selected_option == "Withdraw":
        st.subheader("Withdraw")
        account_number = st.text_input("Enter Account Number")
        amount = st.number_input("Enter Amount to Withdraw")
        if st.button("Withdraw"):
            withdraw(conn, account_number, amount)
    elif selected_option == "Check Balance":
        st.subheader("Check Balance")
        account_number = st.text_input("Enter Account Number")
        if st.button("Check"):
            check_balance(conn, account_number)
    elif selected_option == "Transaction History":
        st.subheader("Transaction History")
        account_number = st.text_input("Enter Account Number")
        if st.button("Check"):
            transaction_history(conn, account_number)
    elif selected_option == "View All Accounts":
        st.subheader("All Accounts")
        display_all_accounts(conn)

if __name__ == "__main__":
    main()
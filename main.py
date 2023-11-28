import gspread as gspread
import pandas as pd
import numpy as np
import panel as pn
import hvplot.pandas
import holoviews as hv
import random

hv.extension('bokeh')
pn.extension("tabulator")

# STEP 1
# Connect to the bank data and clean your transactions

# Option 1: connect to GDrive through API.
# a) create a project in GCfDevelopers -> Enable API for GDrive and GSheets -> Create API Keys (GCD gives a .json file)
# b) move json file to the PyProject directory and rename it to  "service_account.json"
# c) do not forget to share the spreadsheet file (bank transactions) with the "client_email" in service_account.json -

# connect to GDrive through API
g_cred = gspread.service_account(filename="service_account.json")
# open Spreadsheet file with the bank transactions
sheet = g_cred.open("t_transactions")

# read worksheet in the Spreadsheet file
ws = sheet.worksheet("Sheet1")
df = pd.DataFrame(ws.get_all_records())
# a = df.head()
# print(a)

# Option 2 (if you do not like using GoogleApi): import csv file
# filename.csv = file with the bank transactions
# df = pd.read_csv("filename.csv")

# Option 3: create dataset manually

# data = [
#     ['01.09.23', '01.09.23', 1500,  'Вывод средств с брокерского счета'],
#     ['01.09.23', '01.09.23', -350, 'Оплата услуг iBank.MTS']
# ]
#
# columns = ['Transaction Date_Time',	'Transaction Processed', 'Transaction Amount', 'Description']
# df = pd.DataFrame(data=data, columns=columns)
# print(df.head())


# STEP 2: Clean data/df

df = df[['Transaction Processed', 'Transaction Amount', 'Description']]  # we keep only desired columns
# df['Description'] = df['Description'].lower()   # we make Description lower case

df = df.rename(columns={'Transaction Processed': 'Date'})  # rename data column
df = df.rename(columns={'Transaction Amount': 'Amount'})  # rename data column
df['Category'] = "unassigned"  # add Category column to df

# print(df.head())

# STEP 3: Assign categories for transactions (like tags to better see the transactions categories)

# Categories are: Groceries, Shopping, Transport, Travel, Utilities, Cafe, P2P, Others
# we need to assign a category for each transaction (template), using the match in Description string
df['Category'] = np.where(df['Description'].str.contains('TRANSKART.RU|YandexGo', case=False, na=False), 'Transport', df['Category'])
df['Category'] = np.where(df['Description'].str.contains('TATTELECOM|T21V', case=False, na=False), 'Utilities', df['Category'])
df['Category'] = np.where(df['Description'].str.contains('MTS|Tele2', case=False, na=False), 'Mobile', df['Category'])

# Extract the month and year information
df['Date'] = pd.to_datetime(df['Date'], format='%d.%m.%y')
df['Month'] = df['Date'].dt.month
df['Year'] = df['Date'].dt.year

pd.set_option('display.max_columns', None)
print(df.head())

# check unassigned transactions and that they are all within the relevant "unassigned" category
unassigned = df.loc[df['Category'] == 'unassigned']
print(unassigned)

# STEP 4. Create top-banner for the Last Month's income, expenses, and savings

# get the last month and year
most_recent_date = df['Date'].max()
latest_month = most_recent_date.month
latest_year = most_recent_date.year


# filter the DataFrame to include only the transactions from the last month
last_month_expenses = df[(df['Month'] == latest_month) & (df['Year'] == latest_year)]

last_month_expenses = last_month_expenses.groupby('Category')['Amount'].sum().reset_index()

last_month_expenses['Amount'] = last_month_expenses['Amount'].astype('str')
last_month_expenses['Amount'] = last_month_expenses['Amount'].str.replace('-', '') # here we remove '-' from the amounts/expenses items
last_month_expenses['Amount'] = last_month_expenses['Amount'].astype('float')

last_month_expenses = last_month_expenses[last_month_expenses['Category'].str.contains('Excluded|unassigned') == False]
last_month_expenses = last_month_expenses.sort_values(by='Amount', ascending=False)  # sort values
last_month_expenses['Amount'] = last_month_expenses['Amount'].round().astype(int)    # round values

print(last_month_expenses)

last_month_expenses_tot = last_month_expenses['Amount'].sum()
print(last_month_expenses_tot)


def calculate_difference(event):
    income = float(income_widget.value)
    recurring_expenses = float(recurring_expenses_widget.value)
    monthly_expenses = float(monthly_expenses_widget.value)
    difference = income - recurring_expenses - monthly_expenses
    difference_widget.value = str(difference)


income_widget = pn.widgets.TextInput(name="Income", value="0")
recurring_expenses_widget = pn.widgets.TextInput(name="Recurring Expenses", value="0")
monthly_expenses_widget = pn.widgets.TextInput(name="Non-Recurring Expenses", value=str(last_month_expenses_tot))
difference_widget = pn.widgets.TextInput(name="Last Month's Savings", value="0")

income_widget.param.watch(calculate_difference, "value")
recurring_expenses_widget.param.watch(calculate_difference, "value")
monthly_expenses_widget.param.watch(calculate_difference, "value")

#pn.Row(income_widget, recurring_expenses_widget, monthly_expenses_widget, difference_widget).show()

# ## Create last month expenses bar chart

last_month_expenses_chart = last_month_expenses.hvplot.bar(
    x='Category',
    y='Amount',
    height=250,
    width=850,
    title="Last Month Expenses",
    ylim=(0, 500))

# ## Create monthly expenses trend bar chart

df['Date'] = pd.to_datetime(df['Date'])            # convert the 'Date' column to a datetime object
df['Month-Year'] = df['Date'].dt.to_period('M')    # extract the month and year from the 'Date' column and create a new column 'Month-Year'
monthly_expenses_trend_by_cat = df.groupby(['Month-Year', 'Category'])['Amount'].sum().reset_index()

monthly_expenses_trend_by_cat['Amount'] = monthly_expenses_trend_by_cat['Amount'].astype('str')
monthly_expenses_trend_by_cat['Amount'] = monthly_expenses_trend_by_cat['Amount'].str.replace('-','')
monthly_expenses_trend_by_cat['Amount'] = monthly_expenses_trend_by_cat['Amount'].astype('float')
monthly_expenses_trend_by_cat = monthly_expenses_trend_by_cat[monthly_expenses_trend_by_cat["Category"].str.contains("Excluded") == False]

monthly_expenses_trend_by_cat = monthly_expenses_trend_by_cat.sort_values(by='Amount', ascending=False)
monthly_expenses_trend_by_cat['Amount'] = monthly_expenses_trend_by_cat['Amount'].round().astype(int)
monthly_expenses_trend_by_cat['Month-Year'] = monthly_expenses_trend_by_cat['Month-Year'].astype(str)
monthly_expenses_trend_by_cat = monthly_expenses_trend_by_cat.rename(columns={'Amount': 'Amount '})

print(monthly_expenses_trend_by_cat)


#Define Panel widget

select_category1 = pn.widgets.Select(name='Select Category', options=[
    'All', 'Groceries', 'Shopping', 'Transport', 'Travel', 'Utilities', 'Cafe', 'P2P', 'Health', 'Others'
])


# define plot function
def plot_expenses(category):
    if category == 'All':
        plot_df = monthly_expenses_trend_by_cat.groupby('Month-Year').sum()
    else:
        plot_df = monthly_expenses_trend_by_cat[monthly_expenses_trend_by_cat['Category'] == category].groupby('Month-Year').sum()
    plot = plot_df.hvplot.bar(x='Month-Year', y='Amount ')
    return plot


# define callback function
@pn.depends(select_category1.param.value)
def update_plot(category):
    plot = plot_expenses(category)
    return plot

# create layout
monthly_expenses_trend_by_cat_chart = pn.Row(select_category1, update_plot)
monthly_expenses_trend_by_cat_chart[1].width = 600

# ## Create summary table

df = df[['Date', 'Category', 'Description', 'Amount']]
df['Amount'] = df['Amount'].astype('str')
df['Amount']=df['Amount'].str.replace('-', '')
df['Amount'] = df['Amount'].astype('float')        #get absolute figures

df = df[df["Category"].str.contains("Excluded") == False]    #exclude "excluded" category
df['Amount'] = df['Amount'].round().astype(int)      #round values
print(df)


# Define a function to filter the dataframe based on the selected category
def filter_df(category):
    if category == 'All':
        return df
    return df[df['Category'] == category]


# Create a DataFrame widget that updates based on the category filter
summary_table = pn.widgets.DataFrame(filter_df('All'), height=300, width=400)


# Define a callback that updates the dataframe widget when the category filter is changed
def update_summary_table(event):
    summary_table.value = filter_df(event.new)


# Add the callback function to the category widget
select_category1.param.watch(update_summary_table, 'value')


# ## Create Final Dashboard
quotes = ['It is better to look ahead and prepare than to look back and regret', 'Spending money is much more difficult than making money']
quote = random.choice(quotes)

template = pn.template.FastListTemplate(
    title="Personal Finances Summary",
    sidebar=[
        pn.pane.Markdown(f"**{quote}**"),
        pn.pane.PNG('example.png', sizing_mode='scale_both'),
        pn.pane.Markdown(""),
        pn.pane.Markdown(""),
        select_category1
    ],
    main=[
        pn.Row(income_widget, recurring_expenses_widget, monthly_expenses_widget, difference_widget, width=950),
        pn.Row(last_month_expenses_chart, height=240),
        pn.GridBox(
            monthly_expenses_trend_by_cat_chart[1],
            summary_table,
            ncols=2,
            width=500,
            align='start',
            sizing_mode='stretch_width'
        )
    ]
)

template.show()


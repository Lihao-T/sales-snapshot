from pathlib import Path
import pandas as pd
import streamlit as st
from core import clean_sales, summaries, csv_bytes, report_html

st.set_page_config(page_title='Sales Snapshot', page_icon='📊', layout='wide')
st.title('Sales Snapshot')
st.write('Turn a sales CSV into a clear report. No AI API or subscription required.')
st.caption('Local use: files stay in this running app and are not deliberately saved. If deployed online, uploads go to the hosting server.')
file = st.file_uploader('Upload a CSV, or explore the fictional sample below', type=['csv'])
a, b = st.columns(2)
separator = a.selectbox('CSV separator', [',', ';', '\t'], format_func=lambda x: 'Tab' if x == '\t' else x)
encoding = b.selectbox('File encoding', ['utf-8-sig', 'latin-1'])
try:
    raw = pd.read_csv(file, sep=separator, encoding=encoding) if file else pd.read_csv(Path(__file__).parent / 'sample_sales.csv')
except Exception:
    st.error('Could not read this CSV. Check its separator and encoding, then try again.')
    st.stop()
if raw.empty or len(raw.columns) < 4:
    st.error('Include at least one row and four columns: date, product, quantity, line revenue.')
    st.stop()
st.subheader('1. Match your columns')
st.info('Revenue means the total for this sales line, not the unit price. Use one currency per file. This starter handles non-negative sales, not refunds.')
mapping = {}
for col, field in zip(st.columns(4), ['date', 'product', 'quantity', 'revenue']):
    names = list(raw.columns)
    mapping[field] = col.selectbox(field.title(), names, index=names.index(field) if field in names else ['date', 'product', 'quantity', 'revenue'].index(field), key=field)
dayfirst = st.checkbox('Dates use day/month/year (for example 05/10/2026)', value=True)
currency = st.selectbox('Currency label (no conversion)', ['GBP', 'USD', 'EUR', 'CNY'])
try:
    data, rejected = clean_sales(raw, mapping, dayfirst)
except ValueError as error:
    st.warning(str(error))
    st.stop()
if len(rejected):
    st.warning(f'{len(rejected)} of {len(raw)} lines were excluded. Review them before using the report.')
    st.download_button('Download excluded lines', csv_bytes(rejected), 'excluded_lines.csv', 'text/csv')
if data.empty:
    st.error('No valid sales lines remain. Check the column mapping, dates and numbers.')
    st.stop()
st.subheader('2. Your sales overview')
m1, m2, m3 = st.columns(3)
m1.metric('Revenue · ' + currency, f'{data.revenue.sum():,.2f}')
m2.metric('Units sold', f'{data.quantity.sum():,.0f}')
m3.metric('Valid sales lines', len(data))
monthly, products = summaries(data)
left, right = st.columns(2)
with left:
    st.write('Monthly revenue')
    st.bar_chart(monthly.set_index('month')['revenue'])
with right:
    st.write('Top 10 products by revenue')
    st.bar_chart(products.head(10).set_index('product')['revenue'])
st.dataframe(products, hide_index=True, use_container_width=True)
st.caption('Revenue is not profit. Lines are not orders. Duplicate-looking lines are retained because repeated sales may be legitimate.')
st.subheader('3. Download your results')
st.download_button('Cleaned sales CSV', csv_bytes(data), 'cleaned_sales.csv', 'text/csv')
st.download_button('Monthly revenue CSV', csv_bytes(monthly), 'monthly_revenue.csv', 'text/csv')
st.download_button('Product summary CSV', csv_bytes(products), 'product_summary.csv', 'text/csv')
st.download_button('Printable report', report_html(data, currency, len(rejected)), 'sales_report.html', 'text/html')
st.caption('Open the downloaded HTML report in your browser. Choose Print → Save as PDF.')
with st.expander('View valid sales lines'):
    st.dataframe(data, hide_index=True)

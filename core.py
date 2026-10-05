"""Sales calculations; no customer data is sent to an external service."""
import html
import pandas as pd


def clean_sales(raw, mapping, dayfirst=False):
    if len(set(mapping.values())) != 4:
        raise ValueError('Choose four different columns.')
    data = raw[list(mapping.values())].copy()
    data.columns = list(mapping.keys())
    data['date'] = pd.to_datetime(data['date'], errors='coerce', dayfirst=dayfirst, format='mixed')
    data['product'] = data['product'].fillna('').astype(str).str.strip()
    for col in ['quantity', 'revenue']:
        data[col] = pd.to_numeric(data[col], errors='coerce')
    valid = (data['date'].notna() & data['product'].ne('') & data['quantity'].notna()
             & data['revenue'].notna() & data['quantity'].ge(0)
             & data['revenue'].ge(0) & data['quantity'].mod(1).eq(0))
    rejected = raw.loc[~valid].copy()
    rejected['validation_note'] = 'Invalid date/product, non-numeric or negative values, or fractional quantity'
    return data.loc[valid].sort_values('date').reset_index(drop=True), rejected


def summaries(data):
    monthly = data.assign(month=data['date'].dt.strftime('%Y-%m')).groupby('month', as_index=False)['revenue'].sum()
    products = data.groupby('product', as_index=False)[['quantity', 'revenue']].sum().sort_values('revenue', ascending=False)
    return monthly, products


def csv_bytes(data):
    # Prevent spreadsheet applications interpreting user-supplied text as formulas.
    safe = data.copy()
    for col in safe.select_dtypes(include=['object', 'string']).columns:
        safe[col] = safe[col].map(lambda v: "'" + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@')) else v)
    return safe.to_csv(index=False).encode('utf-8-sig')


def report_html(data, currency, excluded):
    monthly, products = summaries(data)
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>Sales report</title>
    <style>body{{font:16px Arial;max-width:900px;margin:40px auto;color:#183047}}table{{border-collapse:collapse;width:100%}}td,th{{padding:10px;border-bottom:1px solid #ddd;text-align:left}}h1{{color:#146c66}}@media print{{body{{margin:15px}}}}</style>
    <h1>Sales report</h1><p>Currency: {html.escape(currency)} | Valid sales lines: {len(data)} | Excluded lines: {excluded}</p>
    <p>Total revenue: {data.revenue.sum():,.2f} | Units sold: {data.quantity.sum():,.0f}</p>
    <p>Period: {data.date.min():%Y-%m-%d} to {data.date.max():%Y-%m-%d}</p>
    <h2>Monthly revenue</h2>{monthly.to_html(index=False, escape=True)}
    <h2>Products ranked by revenue</h2>{products.to_html(index=False, escape=True)}
    <p>Revenue is the supplied line total, not profit. Refunds/negative lines are excluded. No order IDs are supplied, so order count and average order value cannot be calculated. Duplicate-looking lines are retained.</p></html>'''.encode('utf-8')

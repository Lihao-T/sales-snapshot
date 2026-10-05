import unittest
import pandas as pd
from core import clean_sales, summaries, csv_bytes, report_html

MAPPING = dict(zip(['date', 'product', 'quantity', 'revenue'], ['date', 'product', 'quantity', 'revenue']))
class SalesTests(unittest.TestCase):
    def test_sample_totals(self):
        from pathlib import Path
        data, rejected = clean_sales(pd.read_csv(Path(__file__).parent/'sample_sales.csv'), MAPPING)
        self.assertEqual(len(rejected), 0)
        self.assertEqual(data.revenue.sum(), 282)
        self.assertEqual(data.quantity.sum(), 26)
        monthly, products = summaries(data)
        self.assertEqual(monthly.revenue.tolist(), [55, 112, 115])
        self.assertEqual(products.iloc[0]['product'], 'Desk lamp')
    def test_reject_invalid_and_retain_duplicates(self):
        raw = pd.DataFrame([['05/10/2026','Pen',1,3]]*2 + [['bad','Pen',1,3], ['05/10/2026','Pen',-1,3], ['05/10/2026','Pen',1.5,3]], columns=MAPPING)
        data, rejected = clean_sales(raw, MAPPING, True)
        self.assertEqual(len(data), 2)
        self.assertEqual(len(rejected), 3)
        self.assertEqual(data.date.iloc[0].month, 10)
    def test_exports_escape_customer_text(self):
        raw = pd.DataFrame([['2026-10-01','<script>alert(1)</script>',1,2],['2026-10-01','=1+1',1,2]], columns=MAPPING)
        data, _ = clean_sales(raw, MAPPING)
        self.assertNotIn('<script>', report_html(data, 'GBP', 0).decode())
        self.assertIn("'=1+1", csv_bytes(data).decode('utf-8-sig'))
    def test_duplicate_mapping(self):
        with self.assertRaises(ValueError):
            clean_sales(pd.DataFrame(), dict.fromkeys(MAPPING, 'same'))
if __name__ == '__main__':
    unittest.main()

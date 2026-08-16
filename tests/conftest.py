import pandas as pd
import pytest


@pytest.fixture
def messy_sales() -> pd.DataFrame:
    """A small dataset with the same defects as the real export."""
    return pd.DataFrame(
        {
            "Order_ID": ["ORD-1001", "ORD-1002", "ORD-1003", "ORD-1004", "ORD-1004"],
            "Order_Date": [
                "2026-01-10",
                "2026-02-14",
                "1405/02/31",
                "2026-04-02",
                "2026-04-02",
            ],
            "Customer": ["پارس‌ صنعت", "پارس صنعت ", "فولاد جنوب", "فولاد جنوب", "فولاد جنوب"],
            "Province": ["تهران", "اصفهانن", "اصفهان", "تهران", "تهران"],
            "Product_Code": ["P-104", "P-105", "P-104", "P-106", "P-106"],
            "Product": ["فروسیلیس", "کک متالورژی", "فروسیلیس", "بنتونیت", "بنتونیت"],
            "Quantity": [10, 20, 30, 40, 40],
            "Unit_Price_USD": ["1,250.50", "800", "2,000", "1500", "1500"],
            "Discount_Pct": [0, 5, 10, 0, 0],
            "Tax_Pct": ["10%", "10%", "9%", "10%", "10%"],
            "Total_Amount_USD": ["12505 USD", "16000 USD", "60000 USD", "60000 USD", "60000 USD"],
            "Status": ["تکمیل‌ شده", "لغو شده", "در انتظار پرداخت", "تکمیل شده", "تکمیل شده"],
        }
    )

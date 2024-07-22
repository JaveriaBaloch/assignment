from decimal import Decimal

def format_price(price):
    if isinstance(price, Decimal):
        price = str(price)
    return price.strip()

import re
from datetime import datetime
from dateutil.relativedelta import relativedelta

def get_search_ranges():
    today = datetime.now()
    allowed_months = set()
    if today.month == 1:
        return today - relativedelta(months=6), None 
    for i in range(3):
        d = today - relativedelta(months=i)
        allowed_months.add((d.year, d.month))
    target_jan = datetime(today.year, 1, 1)
    if target_jan > today: target_jan -= relativedelta(years=1)
    for d in [target_jan, target_jan - relativedelta(months=1), target_jan - relativedelta(months=2)]:
        allowed_months.add((d.year, d.month))
    oldest = min(allowed_months, key=lambda x: (x[0], x[1]))
    return datetime(oldest[0], oldest[1], 1), allowed_months

def split_message_blocks(text):
    if not text: return []
    if '—' in text: return [b.strip() for b in re.split(r'[-—_]{3,}', text) if b.strip()]
    if len(text) > 500: return [b.strip() for b in text.split('\n\n') if b.strip()]
    return [text]

def extract_price(text, min_price_threshold=0):
    if not text: return None, None
    text_lower = text.lower()
    
    text_cleaned = re.sub(r'(?:em|de|acima de|compras de)\s+(?:r\$)?\s*\d{1,5}(?:[.,]\d{3})*(?:[.,]\d{1,2})?', '', text_lower)
    text_cleaned = re.sub(r'\d+\s?x', '', text_cleaned)

    pattern = r'(?:por|valor|pix|vista|r\$)\s*:?\s*(?:r\$)?\s*(\d{1,5}(?:[.,]\d{3})*(?:[.,]\d{1,2})?)'
    
    matches = re.finditer(pattern, text_cleaned)
    valid_prices = []

    for match in matches:
        val_str = match.group(1)
        
        if ',' in val_str: val_clean = val_str.replace('.', '').replace(',', '.')
        else:
            if val_str.count('.') == 1 and len(val_str.split('.')[1]) == 3: val_clean = val_str.replace('.', '')
            else: val_clean = val_str
        
        try:
            val_float = float(val_clean)
            
            if val_float < 1: continue 
            if val_float in [2024, 2025, 2026]: continue 
            
            if val_float < min_price_threshold: continue

            valid_prices.append((val_float, match.group(0)))     
        except ValueError: continue

    if not valid_prices: return None, None
    return min(valid_prices, key=lambda x: x[0])
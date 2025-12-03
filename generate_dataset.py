import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

nb_lignes = 12000
date_debut = datetime(2024, 1, 1)

instruments = ['EUR/USD', 'GBP/USD', 'USD/CHF', 'EUR/GBP', 'AUD/USD', 'NZD/USD', 
               'EURUSD.FX', 'GBPUSD.FX', 'IRS_EUR_5Y', 'IRS_USD_10Y', 'SWAP_EUR_3M']

banques = ['Goldman Sachs', 'Morgan Stanley', 'JP Morgan', 'Barclays', 'Société Générale', 
           'BNP Paribas', 'Deutsche Bank', 'UBS', 'Credit Suisse', 'Pictet']

statuts = ['EXECUTED', 'PENDING', 'CANCELLED', 'SETTLED', 'CONFIRMED']
types = ['SPOT', 'FORWARD', 'SWAP', 'OPTION', 'NDF']

data = []

for i in range(nb_lignes):
    trade_id = f"TRADE_{i+1:06d}"
    date = date_debut + timedelta(days=random.randint(0, 330))
    instrument = np.random.choice(instruments)
    qty = np.random.normal(loc=1000000, scale=500000)
    prix = np.random.normal(loc=1.1, scale=0.3)
    banque = np.random.choice(banques)
    type_trade = np.random.choice(types)
    statut = np.random.choice(statuts)
    valeur = qty * prix
    
    alea = random.random()
    
    if alea < 0.02:
        qty = np.nan
    elif alea < 0.04:
        qty = np.random.normal(loc=100000000, scale=50000000)
    elif alea < 0.06:
        trade_id = f"TRADE_{max(0, i-random.randint(1, 500)):06d}"
    elif alea < 0.08:
        prix = -abs(prix)
    elif alea < 0.10:
        banque = None
    
    data.append({
        'TradeID': trade_id,
        'Date': date.strftime('%Y-%m-%d'),
        'Instrument': instrument,
        'TradeType': type_trade,
        'Quantity': qty,
        'Price': prix,
        'Value': valeur,
        'Counterparty': banque,
        'Status': statut,
        'Commission': np.random.uniform(0, 0.005) if qty == qty else np.nan,
        'EntryTime': f"{random.randint(9, 17):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}",
        'SettlementDate': (date + timedelta(days=random.randint(1, 5))).strftime('%Y-%m-%d'),
    })

df = pd.DataFrame(data)
df.to_csv('financial_trades_sample.csv', index=False)

print(f"✅ Dataset créé : {len(df)} records")
print(f"\n📊 Preview :")
print(df.head(10))
print(f"\n⚠️ Anomalies détectées :")
print(f"  - Missing Quantity : {df['Quantity'].isna().sum()}")
print(f"  - Missing Counterparty : {df['Counterparty'].isna().sum()}")
print(f"  - Duplicate TradeID : {len(df) - df['TradeID'].nunique()}")
print(f"  - Negative Price : {(df['Price'] < 0).sum()}")
print(f"  - Missing Commission : {df['Commission'].isna().sum()}")

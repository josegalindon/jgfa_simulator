"""
Portfolio configuration with ticker arrays
Generated from final_df.csv based on composite scores
"""

import csv
import os

def load_tickers_from_csv(csv_path='../final_df.csv'):
    """
    Load tickers from CSV and create top100 and bottom100 arrays
    """
    data = []
    csv_full_path = os.path.join(os.path.dirname(__file__), csv_path)

    with open(csv_full_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'Ticker': row['Ticker'],
                'Composite Score': float(row['Composite Score'])
            })

    # Sort by Composite Score in descending order
    data_sorted = sorted(data, key=lambda x: x['Composite Score'], reverse=True)

    # Create top100 array (long positions)
    top100 = [item['Ticker'] for item in data_sorted[:100]]

    # Create bottom100 array (short positions)
    bottom100 = [item['Ticker'] for item in data_sorted[-100:]]

    return top100, bottom100


# Ticker arrays - Top 100 for long positions, Bottom 100 for short positions
TOP_100 = ['AREN', 'AZO', 'ORLY', 'NXXT', 'EPSN', 'NJR', 'FRPH', 'ASC', 'JOUT', 'LPG',
           'RYI', 'MKTX', 'RSVR', 'MTN', 'CHH', 'PTEN', 'CCRD', 'MAMA', 'AGNC', 'AMCX',
           'EFC', 'CSV', 'GRMN', 'SWKH', 'ELA', 'KINS', 'LUCD', 'AIP', 'VRSN', 'AVNT',
           'SPR', 'KREF', 'VLGEA', 'ESNT', 'CACI', 'PRKS', 'BL', 'MPX', 'LVWR', 'SPSC',
           'SFBC', 'CCBG', 'ALG', 'OMC', 'SAFT', 'JAKK', 'PANW', 'LQDT', 'ALKT', 'VGAS',
           'TILE', 'III', 'BJRI', 'CCB', 'NVEC', 'PDEX', 'WD', 'TRAK', 'AVA', 'SNCY',
           'NATR', 'AOS', 'SBFG', 'CSPI', 'FELE', 'INVA', 'PLAY', 'COST', 'SNOW', 'OVBC',
           'CZWI', 'MAS', 'YORW', 'ESI', 'PVLA', 'NABL', 'CRUS', 'GHC', 'JKHY', 'DHT',
           'PLOW', 'PKE', 'EML', 'USPH', 'FUBO', 'NVST', 'CELC', 'HSHP', 'AEHR', 'XYL',
           'ADP', 'HY', 'VICI', 'TUSK', 'HG', 'BNTC', 'AXS', 'STXS', 'ATLO', 'IMAX']

BOTTOM_100 = ['TFC', 'CAPR', 'LYFT', 'JPM', 'FNKO', 'DAVE', 'CART', 'HIMS', 'KRUS', 'LEU',
              'HIPO', 'SLQT', 'AMTB', 'DASH', 'ABCB', 'OLPX', 'CVNA', 'BAC', 'WWW', 'TROX',
              'HYLN', 'ACDC', 'CDTX', 'EU', 'SOUN', 'CZFS', 'SKIL', 'APLD', 'CC', 'ASB',
              'HUMA', 'RH', 'KOD', 'BAND', 'SEI', 'SNV', 'LMND', 'SPWR', 'NU', 'CEG',
              'CRML', 'TSLA', 'PRME', 'CUBI', 'ASPI', 'ENVX', 'PL', 'ACHR', 'FWRD', 'EBS',
              'BEPC', 'RDW', 'WULF', 'RYAM', 'BE', 'GEO', 'COIN', 'REAL', 'LPRO', 'NGNE',
              'RXRX', 'KEY', 'CIFR', 'AFRM', 'HBNC', 'NRG', 'DUOL', 'KFS', 'TRUP', 'CLNE',
              'HOOD', 'TE', 'BBAI', 'EDIT', 'FLYW', 'LUNR', 'AAOI', 'EVLV', 'PTON', 'SMMT',
              'GEVO', 'APP', 'ELF', 'CDZI', 'AIRS', 'SEZL', 'SMHI', 'LNSR', 'SMCI', 'INOD',
              'ISPR', 'PCT', 'UPST', 'DRUG', 'RNAC', 'ETON', 'BKKT', 'AXON', 'UAMY', 'FFAI']

# Portfolio settings
INITIAL_CAPITAL = 100000  # $100,000 starting capital
INCEPTION_DATE = '2025-10-28'  # Portfolio inception date (Tuesday, October 28th)
POSITION_SIZE = 0.01  # 1% per position (1/100)

# Benchmark
BENCHMARK_TICKER = '^GSPC'  # S&P 500

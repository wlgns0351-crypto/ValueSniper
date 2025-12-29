import yfinance as yf
import pandas as pd
import numpy as np
import config
import time

def get_dynamic_multiple(ticker):
    """
    [핵심 로직 수정됨]
    종목별 과거 데이터를 분석해 '동적 적정 배수'를 산출
    
    Logic Change:
    (Old) (과거 평균 + 과거 최저) / 2  -> 너무 보수적이라 기회 놓침
    (New) 과거 4년 평균 (Average Only) -> 상승장 반영하여 기회 포착 확대
    """
    try:
        stock = yf.Ticker(ticker)
        
        # 재무제표 (연간)
        fin = stock.financials.T
        bal = stock.balance_sheet.T
        if fin.empty or bal.empty: return None
        
        # 데이터 병합 및 지표 추출
        fund = pd.merge(fin, bal, left_index=True, right_index=True, how='inner')
        fund.index = pd.to_datetime(fund.index)
        
        if 'EBITDA' in fund.columns:
            ebitda = fund['EBITDA']
        elif 'Normalized EBITDA' in fund.columns:
            ebitda = fund['Normalized EBITDA']
        else:
            ebitda = fund.get('Operating Income', 0)
            
        net_debt = fund.get('Total Debt', 0) - fund.get('Cash And Cash Equivalents', 0)
        shares = stock.info.get('sharesOutstanding', 1)
        
        fund_clean = pd.DataFrame({'EBITDA': ebitda, 'Net_Debt': net_debt, 'Shares': shares})
        fund_clean = fund_clean[fund_clean['EBITDA'] > 0] # 적자 제외
        if fund_clean.empty: return None

        # 주가 데이터 (최근 2년치만 사용해 속도 향상)
        start_date = fund_clean.index[0] - pd.Timedelta(days=365)
        price = yf.download(ticker, start=start_date, progress=False)
        if len(price) == 0: return None
        
        if 'Close' in price.columns: price = price['Close']
        if isinstance(price, pd.DataFrame) and ticker in price.columns: price = price[ticker]
            
        price_df = pd.DataFrame(price).sort_index()
        merged = pd.merge_asof(price_df, fund

import yfinance as yf
import pandas as pd
import numpy as np
import config
import time

def get_dynamic_multiple(ticker):
    """
    [핵심] 종목별 과거 데이터를 분석해 '동적 적정 배수'를 산출
    Logic: (과거 평균 EV/EBITDA + 과거 최저 EV/EBITDA) / 2
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
        merged = pd.merge_asof(price_df, fund_clean, left_index=True, right_index=True, direction='backward')
        
        # 배수 역산
        merged['Daily_EV'] = (merged['Close'] * merged['Shares']) + merged['Net_Debt']
        merged['Multiple'] = merged['Daily_EV'] / merged['EBITDA'].replace(0, np.nan)
        
        valid_mults = merged['Multiple'][(merged['Multiple'] > 0) & (merged['Multiple'] < 100)]
        if len(valid_mults) < 30: return None
        
        # ★ 동적 배수 결정 ★
        avg_mult = valid_mults.mean()
        min_mult = valid_mults.min()
        target_mult = (avg_mult + min_mult) / 2
        
        return {
            'target_mult': target_mult,
            'latest_ebitda': fund_clean['EBITDA'].iloc[0], # 가장 최근 연간 데이터
            'latest_net_debt': fund_clean['Net_Debt'].iloc[0],
            'shares': shares
        }

    except Exception as e:
        return None

def analyze_stock(ticker):
    """개별 종목 진단"""
    try:
        # 1. 동적 데이터 가져오기
        data = get_dynamic_multiple(ticker)
        if not data: return None
        
        # 2. 현재가 가져오기
        price_data = yf.download(ticker, period="1d", progress=False)
        if price_data.empty: return None
        
        current_price = float(price_data['Close'].iloc[-1])
        
        # 3. 적정가 및 진입가 계산
        # 적정가 = (EBITDA * 동적배수 - 순부채) / 주식수
        intrinsic_value = (data['latest_ebitda'] * data['target_mult'] - data['latest_net_debt']) / data['shares']
        
        # 1차 진입가 (안전마진 적용)
        buy_lv1 = intrinsic_value * (1 - config.SAFE_MARGIN)
        
        # 2차 진입가 (물타기 라인 - 1차보다 15% 더 쌀 때)
        buy_lv2 = buy_lv1 * (1 - config.SCALE_IN_DROP)
        
        status = "WATCH"
        signal_msg = ""
        
        # 4. 신호 판별
        if current_price < buy_lv2:
            status = "STRONG_BUY" # 2차 매수 구간 (대바닥)
            upside = (intrinsic_value - current_price) / current_price * 100
            signal_msg = f"🔥 [강력 매수] 바닥 뚫고 지하실! (괴리율 {upside:.1f}%)"
            
        elif current_price < buy_lv1:
            status = "BUY" # 1차 매수 구간
            upside = (intrinsic_value - current_price) / current_price * 100
            signal_msg = f"✅ [1차 매수] 안전마진 확보됨 (괴리율 {upside:.1f}%)"
            
        elif current_price >= intrinsic_value:
            status = "SELL_WARN" # 적정가 도달
            signal_msg = f"⚠️ [매도 주의] 적정가치 도달! 분할 매도 고려."
            
        if status == "WATCH":
            return None # 신호 없으면 조용히 리턴

        return {
            'ticker': ticker,
            'price': current_price,
            'fair_value': intrinsic_value,
            'buy_lv1': buy_lv1,
            'buy_lv2': buy_lv2,
            'target_mult': data['target_mult'],
            'status': status,
            'msg': signal_msg
        }

    except Exception:
        return None

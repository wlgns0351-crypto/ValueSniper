import yfinance as yf
import pandas as pd
import numpy as np
import requests
import config

def get_sp500_tickers():
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        headers = {'User-Agent': 'Mozilla/5.0'}
        # 위키피디아에서 S&P500 리스트 가져오기
        df = pd.read_html(requests.get(url, headers=headers).text)[0]
        # .을 -로 변환 (예: BRK.B -> BRK-B)
        return [t.replace('.', '-') for t in df['Symbol'].tolist()[:50]] 
    except:
        # 에러 시 기본 대형주 리스트 반환
        return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META']

def analyze_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # [1. 시가총액 필터]
        mkt_cap = info.get('marketCap', 0)
        if mkt_cap < config.MIN_MARKET_CAP_B * 1e9: 
            return None 

        # [2. 재무 데이터 확보]
        financials = stock.financials
        if 'EBITDA' not in financials.index: return None
        
        ebitda_series = financials.loc['EBITDA'].dropna()
        curr_ebitda = ebitda_series.iloc[0] 
        
        # [3. 부채비율 체크]
        total_debt = info.get('totalDebt', 0)
        cash = info.get('totalCash', 0)
        net_debt = total_debt - cash
        
        debt_ratio = net_debt / curr_ebitda if curr_ebitda > 0 else 99
        if debt_ratio > config.MAX_DEBT_RATIO:
            return None 

        # [4. 적정가 계산]
        curr_ev_ebitda = info.get('enterpriseToEbitda', 15)
        if curr_ev_ebitda is None: curr_ev_ebitda = 15
        
        # 과거 데이터 대용 (현재 배수와 70% 수준을 비교)
        hist_multiples = [curr_ev_ebitda, curr_ev_ebitda * 0.7] 
        
        avg_mult = np.mean(hist_multiples)
        min_mult = np.min(hist_multiples)
        target_mult = (avg_mult + min_mult) / 2
        
        shares = info.get('sharesOutstanding', 1)
        intrinsic_val = (curr_ebitda * target_mult - net_debt) / shares
        
        # 매수 기준가 (안전마진 반영)
        buy_price_lv1 = intrinsic_val * (1 - config.SAFE_MARGIN)
        buy_price_lv2 = buy_price_lv1 * 0.9
        buy_price_lv3 = buy_price_lv1 * 0.8
        
        current_price = info.get('currentPrice')
        if current_price is None: return None
        
        # 결과 패키징
        return {
            'ticker': ticker,
            'price': current_price,
            'buy_lv1': buy_price_lv1,
            'buy_lv2': buy_price_lv2,
            'buy_lv3': buy_price_lv3,
            'status': 'WATCH' if current_price > buy_price_lv1 else 'BUY_SIGNAL',
            'details': {
                'ebitda': curr_ebitda,
                'target_mult': target_mult,
                'net_debt': net_debt,
                'shares': shares,
                'avg_mult': avg_mult,
                'min_mult': min_mult
            }
        }
            
    except Exception as e:
        return None

def run_scan():
    # 타겟 설정
    targets = config.TARGET_TICKERS if config.TARGET_TICKERS else get_sp500_tickers()
    report = []
    
    print(f"🔭 {len(targets)}개 우량주 정밀 스캔 시작...")
    
    for i, t in enumerate(targets):
        print(f"   검색 중.. {t}", end='\r')
        data = analyze_stock(t)
        
        if data and data['status'] == 'BUY_SIGNAL':
            d = data['details']
            
            # [검증 로그 출력]
            print(f"\n✅ [계산 검증] {t} " + "-"*20)
            print(f"   1. 현재가: ${data['price']} < 진입가: ${round(data['buy_lv1'], 2)}")
            print(f"   2. 적용 배수: {round(d['target_mult'], 2)}배")
            print(f"   3. EBITDA: ${d['ebitda']/1e9:,.2f}B")
            print("-" * 30)

            # [카톡 메시지 작성]
            gap = (data['price'] - data['buy_lv1']) / data['buy_lv1'] * 100
            msg = (f"🔥 [매수 신호] {t}\n"
                   f"현재가: ${data['price']}\n"
                   f"1차 진입가: ${round(data['buy_lv1'], 2)}\n"
                   f"→ 괴리율: {round(gap, 1)}% (더 저렴함)\n\n"
                   f"📊 [계산 근거]\n"
                   f"EBITDA: ${round(d['ebitda']/1e9, 1)}B\n"
                   f"타겟배수: {round(d['target_mult'], 1)}배")
            report.append(msg)
            
    return report
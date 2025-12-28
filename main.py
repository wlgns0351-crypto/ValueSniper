import sniper_logic
import kakao_sender
import config
import requests
import pandas as pd
import time
from datetime import datetime

def get_sp500_tickers():
    """S&P 500 리스트 실시간 확보"""
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        df = pd.read_html(requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).text)[0]
        return [t.replace('.', '-') for t in df['Symbol'].tolist()]
    except:
        # 실패 시 비상용 우량주 리스트
        return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META']

def job():
    print(f"🚀 ValueSniper 가동 시작 ({datetime.now()})")
    
    # 1. 대상 선정
    if config.TARGET_TICKERS == "ALL":
        tickers = get_sp500_tickers()
    else:
        tickers = config.TARGET_TICKERS
        
    print(f"📋 스캔 대상: {len(tickers)}개 종목")
    
    reports = []
    
    # 2. 전수 조사 (Loop)
    for i, ticker in enumerate(tickers):
        # 깃허브 액션 로그에 진행상황 표시 (50개마다)
        if i % 50 == 0: print(f"   ... {i}/{len(tickers)} 분석 중")
        
        result = sniper_logic.analyze_stock(ticker)
        
        if result:
            # 결과 메시지 포맷팅
            msg = (
                f"{result['msg']}\n"
                f"💎 {ticker} (${result['price']:.2f})\n"
                f"적정가: ${result['fair_value']:.2f} (배수 {result['target_mult']:.1f}x)\n"
                f"1차 진입: ${result['buy_lv1']:.2f}\n"
                f"2차 진입: ${result['buy_lv2']:.2f}"
            )
            reports.append(msg)
            print(f"   !!! 신호 포착: {ticker} ({result['status']})")
            
        # 너무 빠른 요청 방지 (딜레이)
        time.sleep(0.1)

    # 3. 카카오톡 전송
    if reports:
        final_msg = f"📢 [ValueSniper] 오늘 포착된 기회 ({len(reports)}건)\n\n" + "\n\n".join(reports)
        # 카톡 길이 제한 고려 (너무 길면 잘라서 보냄)
        if len(final_msg) > 1000:
            final_msg = final_msg[:950] + "\n... (내용이 너무 많아 생략됨)"
            
        kakao_sender.send_kakao_msg(final_msg)
        print("✅ 리포트 전송 완료")
    else:
        print("💤 오늘 조건에 맞는 종목 없음.")
        # 생존 신고 (선택 사항)
        kakao_sender.send_kakao_msg("💤 [ValueSniper] 오늘은 쉴게요. (조건 만족 종목 없음)")

if __name__ == "__main__":
    job()

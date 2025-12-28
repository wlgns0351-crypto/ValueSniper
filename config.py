KAKAO_API_KEY = "SECRET"

# [ValueSniper 설정 파일]

# 1. 안전마진 (할인율)
# 0.2 = 적정가보다 20% 싸야 산다
SAFE_MARGIN = 0.2

# 2. 분할 매수 설정 (물타기 기준)
# 1차 매수 후 15% 더 떨어지면 2차 매수 신호 보냄
SCALE_IN_DROP = 0.15 

# 3. 대상 종목
# "ALL"로 쓰면 S&P 500 전 종목을 스캔합니다. (시간 소요됨)
# 특정 종목만 보려면 리스트로 적으세요. 예: ["GOOGL", "TSLA", "AAPL"]
TARGET_TICKERS = "ALL"

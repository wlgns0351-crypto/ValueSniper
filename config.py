# 투자 원칙 설정
INITIAL_SEED = 10000        # 총 시드머니 ($)
SAFE_MARGIN = 0.2           # 안전마진 20%
STOP_LOSS_RATE = -0.1       # 손절 기준 (-10%)
TAKE_PROFIT_RATE = 0.2      # 익절 기준 (+20%)

# 스크리닝 필터 (강화된 기능)
MIN_MARKET_CAP_B = 10       # 시가총액 최소 100억 달러 이상 (잡주 제외)
MAX_DEBT_RATIO = 2.0        # 부채비율(부채/EBITDA) 2배 이하 (재무 건전성)
TARGET_TICKERS = []         # 비워두면 S&P500 상위 종목 자동 스캔, ['AMZN', 'GOOGL'] 처럼 지정 가능

# [NEW] 카카오 REST API 키 (내 애플리케이션 > 앱 키 > REST API 키)
KAKAO_API_KEY = "cde60114fe6475f79154e23cc81d27e0"
import sniper_logic
import kakao_sender
from datetime import datetime

def job():
    print("\n" + "="*40)
    print(f"🚀 ValueSniper 가동 시작 ({datetime.now()})")
    print("="*40)

    # 1. 스캔 실행
    signals = sniper_logic.run_scan()
    
    # 2. 결과 처리
    if signals:
        full_msg = f"📢 [ValueSniper] 긴급 포착 ({len(signals)}건)\n\n" + "\n\n".join(signals)
        print("\n✅ 매수 대상 발견! 카톡 전송 중...")
        kakao_sender.send_kakao_msg(full_msg)
    else:
        print("\n💤 현재 조건에 맞는 저평가 우량주가 없습니다.")
        # (선택) 생존신고 메시지 보내기
        # kakao_sender.send_kakao_msg("봇 생존 신고: 특이사항 없음")

if __name__ == "__main__":
    job()
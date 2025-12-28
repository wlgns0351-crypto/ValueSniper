import requests
import json
import os
import sys

def send_kakao_msg(text):
    # ------------------------------------------------------------------
    # [클라우드 전용] 파일이 아니라 깃허브 Secrets에서 키를 가져옵니다.
    # ------------------------------------------------------------------
    api_key = os.environ.get("KAKAO_API_KEY")
    refresh_token = os.environ.get("KAKAO_REFRESH_TOKEN")

    if not api_key or not refresh_token:
        print("❌ [오류] 깃허브 Secrets(환경변수)가 설정되지 않았습니다.")
        print("   -> Settings > Secrets and variables > Actions에 키가 있는지 확인하세요.")
        return

    # 1. 리프레시 토큰으로 '새로운 액세스 토큰' 발급
    # (파일을 저장하지 않고 매번 새로 받아서 씁니다)
    url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": api_key,
        "refresh_token": refresh_token
    }
    
    response = requests.post(url, data=data)
    tokens = response.json()

    if "access_token" not in tokens:
        print("❌ 토큰 갱신 실패! (리프레시 토큰 만료 가능성)")
        print(f"응답 내용: {tokens}")
        return

    access_token = tokens["access_token"]

    # 2. 메시지 전송
    send_url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": "Bearer " + access_token}
    payload = {
        "template_object": json.dumps({
            "object_type": "text",
            "text": text,
            "link": {"web_url": "https://finance.yahoo.com"}
        })
    }
    
    res = requests.post(send_url, headers=headers, data=payload)
    
    if res.json().get('result_code') == 0:
        print("✅ [성공] 카톡 전송 완료!")
    else:
        print("❌ 전송 실패:", res.json())

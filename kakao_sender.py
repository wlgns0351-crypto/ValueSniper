import requests
import json
import os
import config  # API 키를 가져오기 위해 필요

TOKEN_FILE = "data/kakao_token.json"

def save_tokens(tokens):
    with open(TOKEN_FILE, "w") as fp:
        json.dump(tokens, fp)

def load_tokens():
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE, "r") as fp:
        return json.load(fp)

# kakao_sender.py 안의 refresh_token 함수를 이것으로 교체하세요

def refresh_token(tokens):
    url = "https://kapi.kakao.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": config.KAKAO_API_KEY,
        "refresh_token": tokens["refresh_token"]
    }
    
    print("🔄 토큰 갱신 요청 중...") # 로그 추가
    response = requests.post(url, data=data)
    
    try:
        result = response.json()
    except:
        print(f"❌ [치명적 오류] 서버 응답을 읽을 수 없습니다. 응답 내용: {response.text}")
        return False

    # [수정] result가 딕셔너리가 아닌 경우(숫자 등) 방어 코드
    if not isinstance(result, dict):
        print(f"❌ [오류] 서버가 이상한 응답을 보냈습니다 (타입: {type(result)}): {result}")
        print("   -> 힌트: config.py의 API 키가 정확한지 확인하세요.")
        return False

    # 갱신 성공 시
    if 'access_token' in result:
        tokens['access_token'] = result['access_token']
        if 'refresh_token' in result:
            tokens['refresh_token'] = result['refresh_token']
        save_tokens(tokens)
        print("✅ 토큰 갱신 성공!")
        return True
    else:
        # 에러 메시지 출력
        error_code = result.get('error')
        error_desc = result.get('error_description')
        print(f"❌ 토큰 갱신 실패! (에러: {error_code})")
        print(f"   설명: {error_desc}")
        
        if error_code == 'invalid_client':
            print("   -> 힌트: config.py의 KAKAO_API_KEY가 틀렸거나 따옴표가 없습니다.")
        elif error_code == 'invalid_grant':
            print("   -> 힌트: 토큰 유효기간(Refresh Token)이 완전히 만료되었습니다. 재발급이 필요합니다.")
            
        return False

def send_kakao_msg(text):
    tokens = load_tokens()
    if tokens is None:
        print("❌ [오류] data 폴더에 kakao_token.json이 없습니다.")
        return

    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": "Bearer " + tokens["access_token"]}
    data = {
        "template_object": json.dumps({
            "object_type": "text",
            "text": text,
            "link": {"web_url": "https://finance.yahoo.com"}
        })
    }
    
    response = requests.post(url, headers=headers, data=data)
    
    # 401 Unauthorized 에러가 뜨면 토큰이 만료된 것임 -> 갱신 시도
    if response.status_code == 401:
        print("⚠️ 토큰 만료 감지! 갱신을 시도합니다...")
        if refresh_token(tokens):
            # 갱신 성공했으니 재귀호출로 다시 전송 시도
            send_kakao_msg(text)
        else:
            print("❌ 토큰 갱신에 실패했습니다. 수동 재발급이 필요합니다.")
            
    elif response.json().get('result_code') == 0:
        print("✅ 카톡 전송 성공!")
    else:
        print(f"❌ 전송 실패 (에러코드: {response.status_code})")
import requests
from .models import Member
import json

def fetch_and_save_mainsource():
    api_url = "https://open.assembly.go.kr/portal/openapi/nwvrqwxyaytdsfvhu"
    api_key = "927928bf24af47d4afa7b805ed0bf4fc"

    params = {
        "KEY": api_key,
        "Type": "json",
        "pIndex": "1",
        "pSize": "300"
    }

    response = requests.get(api_url, params=params)

    if response.status_code != 200:
        print(f"API 요청 실패: {response.status_code}")
        return

    try:
        data = response.json()
        api_data = data.get("nwvrqwxyaytdsfvhu", [])

        if len(api_data) < 2:
            print("API 데이터 구조가 예상과 다릅니다.")
            return

        rows = api_data[1].get("row", [])
        if not isinstance(rows, list):
            print("'row' 키가 없거나 리스트 형식이 아닙니다.")
            return

        print(f"👨‍💼 총 {len(rows)}명의 국회의원 데이터를 가져왔습니다.")

        for row in rows:
            mona_cd_value = row.get("MONA_CD", "") or ""  # ✅ None일 경우 빈 문자열로 처리

            if not mona_cd_value.strip():
                print(f"❌ `MONA_CD` 값이 비어 있습니다. 해당 데이터는 저장되지 않습니다.")
                continue

            homepage_value = row.get("HOMEPAGE", "") or ""  # ✅ None이면 빈 문자열 처리
            homepage_value = homepage_value.strip() if homepage_value else None  # ✅ 빈 값 처리

            email_value = row.get("E_MAIL", "") or ""  # ✅ None이면 빈 문자열 처리
            email_value = email_value.strip() if email_value else None  # ✅ 빈 값 처리

            Member.objects.update_or_create(
                mona_cd=mona_cd_value,
                defaults={
                    "name": row.get("HG_NM", "") or "",
                    "party": row.get("POLY_NM", "") or "",
                    "committees": row.get("CMITS", "") or "",
                    "phone": row.get("TEL_NO", "") or "",
                    "email": email_value,  # ✅ 안전하게 None 처리
                    "homepage": homepage_value  # ✅ 안전하게 None 처리
                }
            )

        print("🎉 국회의원 정보 저장 완료!")

    except json.JSONDecodeError:
        print("❌ JSON 파싱 실패")
        print(response.text[:1000])  # 오류 확인을 위한 출력
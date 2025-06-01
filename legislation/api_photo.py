import requests
from legislation.models import Photo

api_key = "927928bf24af47d4afa7b805ed0bf4fc"
api_url = "https://open.assembly.go.kr/portal/openapi/ALLNAMEMBER"

def fetch_and_store_members():
    params = {
        "KEY": api_key,
        "Type": "json",
        "pIndex": "1",
        "pSize": "300",
        "age": "22"
    }

    response = requests.get(api_url, params=params)

    if response.status_code == 200:
        data = response.json()

        if len(data) == 1:  
            root_key = next(iter(data))
            items = data.get(root_key, [])

            if len(items) > 1 and "row" in items[1]:
                rows = items[1]["row"]

                for row in rows:
                    member_code = row.get("NAAS_CD", "")
                    member_name = row.get("NAAS_NM", "")
                    photo_url = row.get("NAAS_PIC", "")

                    print(f"🔍 사진 URL 확인: {photo_url}")

                    # ✅ 사진 URL을 그대로 DB에 저장
                    Photo.objects.update_or_create(
                        member_code=member_code,
                        defaults={
                            "member_name": member_name,
                            "photo": photo_url  # 🔹 파일 대신 URL을 저장
                        }
                    )

    print(f"✅ 총 {Photo.objects.count()}명의 의원 정보와 사진 URL이 저장되었습니다.")
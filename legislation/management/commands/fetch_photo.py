from django.core.management.base import BaseCommand
from legislation.api_photo import fetch_and_store_members

class Command(BaseCommand):
    help = "Fetch and store Assembly Members with photos"

    def handle(self, *args, **kwargs):
        fetch_and_store_members()
        self.stdout.write(self.style.SUCCESS("✅ 국회의원 정보 및 사진 저장 완료!"))
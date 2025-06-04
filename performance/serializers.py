from rest_framework import serializers
from performance.models import Performance,PartyPerformance

class PerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Performance
        fields = "__all__"

class PartyPerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartyPerformance
        fields = "__all__"  # ✅ 모든 필드를 자동으로 반환하도록 변경



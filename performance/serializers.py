from rest_framework import serializers
from performance.models import Performance

class PerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Performance
        fields = "__all__"

class PartyPerformanceSerializer(serializers.Serializer):
    party = serializers.CharField()
    avg_score = serializers.FloatField()
    count = serializers.IntegerField()
    weighted_score = serializers.FloatField()



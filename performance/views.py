from rest_framework.response import Response
from rest_framework.decorators import api_view
from performance.models import Performance, PartyPerformance
from legislation.models import Member
from performance.serializers import PerformanceSerializer, PartyPerformanceSerializer
import math

@api_view(["GET"])
def get_performance_data(request):
    """총 실적 점수를 사용자의 입력에 따라 정렬하여 반환 (현재 국회의원만 필터링)"""
    order = request.GET.get("order", "desc")  # 기본값: 내림차순(desc)
    limit = int(request.GET.get("limit", 10))  # 기본값: 10개 출력

    if order not in ("asc", "desc"):
        return Response({"error": "⚠️ 정렬 방식은 'asc' 또는 'desc' 중 하나여야 합니다."}, status=400)

    order_by = "total_score" if order == "asc" else "-total_score"

    # 현재 국회의원 목록 가져오기
    current_lawmaker_names = Member.objects.values_list("name", flat=True)

    # 현재 국회의원만 포함하여 정렬
    performances = Performance.objects.filter(lawmaker__name__in=current_lawmaker_names).order_by(order_by)[:limit]

    if not performances.exists():
        return Response({"message": "❌ 실적 데이터가 없습니다."}, status=404)

    serializer = PerformanceSerializer(performances, many=True)
    return Response({"ranking": serializer.data})

@api_view(["GET"])
def get_party_weighted_performance(request):
    """가중치를 반영한 정당별 실적 점수를 DB에서 조회하여 반환"""
    order = request.GET.get("order", "desc")  # 기본: 내림차순

    if order not in ("asc", "desc"):
        return Response({"error": "⚠️ 정렬 방식은 'asc' 또는 'desc' 중 하나여야 합니다."}, status=400)

    stats = PartyPerformance.objects.all().order_by(
        "weighted_score" if order == "asc" else "-weighted_score"
    )

    if not stats.exists():
        return Response({"message": "❌ 정당 통계 데이터가 없습니다."}, status=404)

    serializer = PartyPerformanceSerializer(stats, many=True)
    return Response({"party_ranking": serializer.data})

@api_view(["GET"])
def get_party_performance_stats(request):
    """정당별 통계 전체 목록 조회"""
    stats = PartyPerformance.objects.all().order_by("-weighted_score")
    serializer = PartyPerformanceSerializer(stats, many=True)
    return Response({"party_stats": serializer.data})

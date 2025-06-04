import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from performance.models import Performance
from vote.models import Lawmaker, LawmakerVoteSummary
from legislation.models import Petition, Member, PetitionIntroducer, CommitteeMember
from attendance.models import Attendance
from performance.party_stats import calculate_party_performance_scores  # 정당 실적 계산 함수 가져오기

# 기본 가중치
DEFAULT_WEIGHTS = {
    "attendance_weight": 8.0,
    "bill_passed_weight": 40.0,
    "petition_proposed_weight": 8.0,
    "petition_result_weight": 23.0,
    "committee_weight": 5.0,
    "adjusted_invalid_vote_weight": 2.0,
    "vote_match_weight": 7.0,
    "vote_mismatch_weight": 4.0,
    "max_invalid_vote_score": 4.0,
}

def calculate_performance_scores(weights=None):
    """국회의원 실적을 계산하고 사용자 입력이 없으면 기본 가중치를 사용"""
    final_weights = weights if weights else DEFAULT_WEIGHTS

    all_lawmakers = Lawmaker.objects.all()
    raw_scores = {}

    for lawmaker in all_lawmakers:
        name = lawmaker.name
        attendance_score = get_attendance_score(name)
        invalid_vote_ratio = get_invalid_vote_ratio(name)
        vote_match_ratio = get_vote_match_ratio(name)

        total_score = (
            attendance_score * (final_weights["attendance_weight"] / 100) +
            invalid_vote_ratio * (-final_weights["adjusted_invalid_vote_weight"] / 100) +
            vote_match_ratio * (final_weights["vote_match_weight"] / 100)
        )

        raw_scores[name] = total_score

    for lawmaker in all_lawmakers:
        name = lawmaker.name
        Performance.objects.update_or_create(
            lawmaker=lawmaker,
            defaults={
                "total_score": raw_scores[name],
                "attendance_score": get_attendance_score(name),
                "invalid_vote_ratio": get_invalid_vote_ratio(name),
                "vote_match_ratio": get_vote_match_ratio(name),
            }
        )

    print("✅ 국회의원 실적 업데이트 완료!")

@csrf_exempt
def update_weights_and_recalculate(request):
    """사용자 입력에 따라 국회의원 및 정당 실적 업데이트"""
    if request.method == "POST":
        data = json.loads(request.body)

        # 사용자 입력이 없으면 기본 가중치 사용
        weights = data if data else DEFAULT_WEIGHTS

        calculate_performance_scores(weights)  # 국회의원 실적 업데이트
        calculate_party_performance_scores(weights)  # 정당 실적 업데이트

        return JsonResponse({"message": "✅ 실적 업데이트 완료! (사용자 입력 반영됨)"})
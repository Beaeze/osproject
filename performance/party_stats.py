import numpy as np
from django.db.models import Avg, Sum
from performance.models import PartyPerformance, Performance
from legislation.models import Member, CommitteeMember

# 기본 가중치 (국회의원 실적 방식 적용)
DEFAULT_WEIGHTS = {
    "attendance_weight": 8.0,
    "bill_passed_weight": 40.0,
    "petition_proposed_weight": 8.0,
    "petition_result_weight": 23.0,
    "committee_weight": 5.0,
    "adjusted_invalid_vote_weight": 2.0,
    "vote_match_weight": 7.0,
    "vote_mismatch_weight": 4.0,
}

def calculate_party_performance_scores(weights=None):
    """국회의원 실적을 기반으로 정당 실적을 계산하고, 사용자 입력이 없으면 기본 가중치를 사용"""
    final_weights = weights if weights else DEFAULT_WEIGHTS

    party_stats = Member.objects.values("party").distinct()  # 정당 목록 가져오기

    for party_obj in party_stats:
        party_name = party_obj["party"]

        # 🔥 `Performance` 모델을 활용하여 정당별 국회의원 점수 가져오기
        performances = Performance.objects.filter(party=party_name)

        # 각 요소별 평균 점수 계산
        avg_attendance = performances.aggregate(Avg("attendance_score"))["attendance_score__avg"] or 0.0
        avg_bill_pass = performances.aggregate(Avg("bill_pass_score"))["bill_pass_score__avg"] or 0.0
        avg_petition = performances.aggregate(Avg("petition_score"))["petition_score__avg"] or 0.0
        avg_petition_result = performances.aggregate(Avg("petition_result_score"))["petition_result_score__avg"] or 0.0
        avg_committee = performances.aggregate(Avg("committee_score"))["committee_score__avg"] or 0.0
        avg_invalid_vote = performances.aggregate(Avg("invalid_vote_ratio"))["invalid_vote_ratio__avg"] or 0.0
        avg_vote_match = performances.aggregate(Avg("vote_match_ratio"))["vote_match_ratio__avg"] or 0.0
        avg_vote_mismatch = performances.aggregate(Avg("vote_mismatch_ratio"))["vote_mismatch_ratio__avg"] or 0.0

        # 🔥 정당 실적 종합 점수(`weighted_score`) 계산 (국회의원 실적 가중치 적용)
        weighted_score = round(
            avg_attendance * (final_weights["attendance_weight"] / 100) +
            avg_bill_pass * (final_weights["bill_passed_weight"] / 100) +
            avg_petition * (final_weights["petition_proposed_weight"] / 100) +
            avg_petition_result * (final_weights["petition_result_weight"] / 100) +
            avg_committee * (final_weights["committee_weight"] / 100) +
            avg_invalid_vote * (-final_weights["adjusted_invalid_vote_weight"] / 100) + 
            avg_vote_match * (final_weights["vote_match_weight"] / 100) +
            avg_vote_mismatch * (final_weights["vote_mismatch_weight"] / 100), 2
        )

        # 🔥 위원장 및 간사 수 (`CommitteeMember` 모델 활용)
        committee_leader_count = CommitteeMember.objects.filter(
            POLY_NM=party_name,
            JOB_RES_NM="위원장"
        ).count()

        committee_secretary_count = CommitteeMember.objects.filter(
            POLY_NM=party_name,
            JOB_RES_NM="간사"
        ).count()

        # 정당별 의원 수
        member_count = performances.count()

        # 데이터 저장 또는 업데이트
        PartyPerformance.objects.update_or_create(
            party=party_name,
            defaults={
                "avg_attendance": round(avg_attendance, 2),
                "avg_invalid_vote_ratio": round(avg_invalid_vote, 2),
                "avg_vote_match_ratio": round(avg_vote_match, 2),
                "avg_vote_mismatch_ratio": round(avg_vote_mismatch, 2),
                "bill_pass_sum": performances.aggregate(Sum("bill_pass_score"))["bill_pass_score__sum"] or 0,
                "petition_sum": performances.aggregate(Sum("petition_score"))["petition_score__sum"] or 0,
                "petition_pass_sum": performances.aggregate(Sum("petition_result_score"))["petition_result_score__sum"] or 0,
                "committee_leader_count": committee_leader_count,
                "committee_secretary_count": committee_secretary_count,
                "member_count": member_count,
                "weighted_score": weighted_score
            }
        )

    print("✅ 정당 실적 업데이트 완료!")
import numpy as np
from django.db.models import Sum, Max
from performance.models import PartyPerformance, Performance
from legislation.models import CommitteeMember, Member

# 기본 가중치를 간사와 위원장으로 분리
DEFAULT_WEIGHTS = {
    "attendance_weight": 8.0,
    "bill_passed_weight": 40.0,
    "petition_proposed_weight": 8.0,
    "petition_result_weight": 23.0,
    "chairman_weight": 5.0,      # 위원장 가중치
    "secretary_weight": 3.0,   # 간사 가중치 (기존 5.0에서 분리)
    "adjusted_invalid_vote_weight": 2.0,
    "vote_match_weight": 7.0,
    "vote_mismatch_weight": 4.0,
}

MIN_MEMBER_THRESHOLD = 10
PENALTY_RATIO = 0.5

def calculate_party_performance_scores(weights=None):
    final_weights = weights if weights else DEFAULT_WEIGHTS
    party_stats = Member.objects.values("party").distinct()

    for party_obj in party_stats:
        party_name = party_obj["party"]
        performances = Performance.objects.filter(party=party_name)
        member_count = performances.count()

        if member_count == 0:
            continue

        total_attendance = performances.aggregate(Sum("attendance_score"))["attendance_score__sum"] or 0.0
        total_bill_pass = performances.aggregate(Sum("bill_pass_count"))["bill_pass_count__sum"] or 0.0
        total_petition = performances.aggregate(Sum("petition_score"))["petition_score__sum"] or 0.0
        total_petition_result = performances.aggregate(Sum("petition_result_score"))["petition_result_score__sum"] or 0.0
        total_committee_leader = performances.aggregate(Sum("committee_leader_score"))["committee_leader_score__sum"] or 0.0
        total_committee_secretary = performances.aggregate(Sum("committee_secretary_score"))["committee_secretary_score__sum"] or 0.0
        total_invalid_vote = performances.aggregate(Sum("invalid_vote_ratio"))["invalid_vote_ratio__sum"] or 0.0
        total_vote_match = performances.aggregate(Sum("vote_match_ratio"))["vote_match_ratio__sum"] or 0.0
        total_vote_mismatch = performances.aggregate(Sum("vote_mismatch_ratio"))["vote_mismatch_ratio__sum"] or 0.0

        max_invalid_ratio = performances.aggregate(Max("invalid_vote_ratio"))["invalid_vote_ratio__max"] or 1.0
        if max_invalid_ratio == 0:
            max_invalid_ratio = 1.0

        normalized_invalid_score = 1.0 - (total_invalid_vote / (member_count * max_invalid_ratio))
        normalized_invalid_score = max(0.0, normalized_invalid_score)

        # 로그 변환 점수 계산 - 간사, 위원장 가중치 분리 적용
        att_score = np.log(total_attendance + 1) * (final_weights["attendance_weight"] / 100)
        bill_pass_score = np.log(total_bill_pass + 1) * (final_weights["bill_passed_weight"] / 100)
        petition_score = np.log(total_petition + 1) * (final_weights["petition_proposed_weight"] / 100)
        petition_result_score = np.log(total_petition_result + 1) * (final_weights["petition_result_weight"] / 100)
        committee_leader_score = np.log(total_committee_leader + 1) * (final_weights["chairman_weight"] / 100)
        committee_secretary_score = np.log(total_committee_secretary + 1) * (final_weights["secretary_weight"] / 100)
        vote_match_score = np.log(total_vote_match + 1) * (final_weights["vote_match_weight"] / 100)
        vote_mismatch_score = np.log(total_vote_mismatch + 1) * (final_weights["vote_mismatch_weight"] / 100)
        invalid_vote_score = np.log(normalized_invalid_score + 1) * (final_weights["adjusted_invalid_vote_weight"] / 100)

        score_items = [
            att_score,
            bill_pass_score,
            petition_score,
            petition_result_score,
            committee_leader_score,
            committee_secretary_score,
            vote_match_score,
            vote_mismatch_score,
            invalid_vote_score,
        ]

        score_total = sum(score_items)

        if member_count < MIN_MEMBER_THRESHOLD:
            penalty_factor = PENALTY_RATIO
        else:
            penalty_factor = 1.0

        weighted_score = round(score_total * penalty_factor, 2)

        # 비중(%): 점수 합 기준으로 비율 계산 → 항상 0 이상 & 합이 100%
        if score_total > 0:
            pct_list = [round(s / score_total * 100, 2) for s in score_items]
            diff = round(100.0 - sum(pct_list), 2)
            pct_list[-1] += diff  # 마지막 항목에 보정
        else:
            pct_list = [0.0] * len(score_items)

        (
            attendance_pct,
            bill_pass_pct,
            petition_pct,
            petition_result_pct,
            committee_leader_pct,
            committee_secretary_pct,
            vote_match_pct,
            vote_mismatch_pct,
            invalid_vote_pct,
        ) = pct_list

        # 위원장 / 간사 중복 제외 처리
        committee_leader_members = CommitteeMember.objects.filter(
            POLY_NM=party_name, JOB_RES_NM="위원장"
        ).values_list("HG_NM", flat=True).distinct()

        committee_secretary_members = CommitteeMember.objects.filter(
            POLY_NM=party_name, JOB_RES_NM="간사"
        ).values_list("HG_NM", flat=True).distinct()

        committee_secretary_members = [m for m in committee_secretary_members if m not in committee_leader_members]

        committee_leader_count = len(committee_leader_members)
        committee_secretary_count = len(committee_secretary_members)

        avg_total_score = performances.aggregate(Sum("total_score"))["total_score__sum"] or 0.0
        avg_total_score /= member_count

        PartyPerformance.objects.update_or_create(
            party=party_name,
            defaults={
                "avg_attendance": round(total_attendance / member_count, 2),
                "avg_invalid_vote_ratio": round(total_invalid_vote / member_count, 2),
                "avg_vote_match_ratio": round(total_vote_match / member_count, 2),
                "avg_vote_mismatch_ratio": round(total_vote_mismatch / member_count, 2),
                "bill_pass_sum": total_bill_pass,
                "petition_sum": total_petition,
                "petition_pass_sum": total_petition_result,
                "committee_leader_count": committee_leader_count,
                "committee_secretary_count": committee_secretary_count,
                "member_count": member_count,
                "weighted_score": weighted_score,
                "avg_total_score": round(avg_total_score, 2),

                "attendance_pct": attendance_pct,
                "bill_pass_pct": bill_pass_pct,
                "petition_pct": petition_pct,
                "petition_result_pct": petition_result_pct,
                "committee_leader_pct": committee_leader_pct,
                "committee_secretary_pct": committee_secretary_pct,
                "vote_match_pct": vote_match_pct,
                "vote_mismatch_pct": vote_mismatch_pct,
                "invalid_vote_pct": invalid_vote_pct,
            }
        )

    print("✅ 정당 실적 및 기여도 업데이트 완료!")

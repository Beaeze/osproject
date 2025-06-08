from vote.models import Lawmaker, LawmakerVoteSummary
from legislation.models import (
    Petition, Member, PetitionIntroducer, CommitteeMember, Bill_count
)
from attendance.models import Attendance
from .models import Performance

# 가결 처리 코드
GAEOL_LIST = ["원안가결", "수정가결", "대안반영가결", "임시가결"]

# 기본 가중치 (만점 100 기준 각 항목별 최고점)
DEFAULT_WEIGHTS = {
    "attendance_weight": 8.0,
    "bill_passed_weight": 40.0,
    "petition_proposed_weight": 8.0,
    "petition_result_weight": 23.0,
    "committee_weight": 5.0,
    "adjusted_invalid_vote_weight": 2.0,
    "vote_match_weight": 7.0,
    "vote_mismatch_weight": 4.0,
    "max_invalid_vote_score": 2.0,
}

def load_party_info():
    return {m.name: m.party for m in Member.objects.all()}

def get_attendance_score(name):
    rec = Attendance.objects.filter(member_name=name).first()
    return round(rec.attendance_rate, 2) if rec else 0.0

def get_invalid_vote_ratio(name):
    s = LawmakerVoteSummary.objects.filter(lawmaker__name=name).first()
    if s and s.total_votes:
        return round(s.invalid_or_abstain_count / s.total_votes * 100, 2)
    return 0.0

def get_adjusted_invalid_vote_score(name, max_score):
    ratio = get_invalid_vote_ratio(name)
    score = max_score * (1 - ratio / 100)
    return round(score, 2)

def get_vote_match_ratio(name):
    s = LawmakerVoteSummary.objects.filter(lawmaker__name=name).first()
    if s:
        total = s.agree_count + s.oppose_count
        match = s.agree_and_passed + s.oppose_and_failed
        return round(match / total * 100, 2) if total else 0.0
    return 0.0

def get_vote_mismatch_ratio(name):
    s = LawmakerVoteSummary.objects.filter(lawmaker__name=name).first()
    if s:
        total = s.agree_count + s.oppose_count
        mismatch = s.agree_and_failed + s.oppose_and_passed
        return round(mismatch / total * 100, 2) if total else 0.0
    return 0.0

def get_petition_count(name):
    return PetitionIntroducer.objects.filter(introducer_name=name).count()

def get_petition_pass_count(name):
    p_ids = PetitionIntroducer.objects.filter(introducer_name=name).values_list("petition_id", flat=True)
    return Petition.objects.filter(BILL_ID__in=p_ids, PROC_RESULT_CD__in=GAEOL_LIST).count()

def get_committee_score(name):
    leader_count = CommitteeMember.objects.filter(HG_NM=name, JOB_RES_NM="위원장").count()
    secretary_count = CommitteeMember.objects.filter(HG_NM=name, JOB_RES_NM="간사").count()
    # 위원장과 간사 둘 다면 최대 5점으로 동일 처리
    if leader_count > 0 and secretary_count > 0:
        score = 5
    else:
        score = 5 * leader_count + 3 * secretary_count
    return score, leader_count, secretary_count

def get_bill_pass_count(name):
    bc = Bill_count.objects.filter(proposer=name).first()
    return bc.approved if bc else 0

def get_bill_total(name):
    bc = Bill_count.objects.filter(proposer=name).first()
    return bc.total if bc else 0

def normalize_scores(scores, max_value=100):
    max_score = max(scores.values()) if scores else 1
    if max_score == 0:
        max_score = 1
    return {k: round((v / max_score) * max_value, 2) for k, v in scores.items()}

def calculate_performance_scores(**weights):
    final_weights = {**DEFAULT_WEIGHTS, **weights}
    party_map = load_party_info()
    all_lawmakers = Lawmaker.objects.all()

    # Petition 관련 총 수 집계
    TOTAL_PETITIONS = PetitionIntroducer.objects.values("petition_id").distinct().count()
    TOTAL_PASSED_PETITIONS = Petition.objects.filter(PROC_RESULT_CD__in=GAEOL_LIST).values("BILL_ID").distinct().count()

    raw_scores = {}

    for lw in all_lawmakers:
        name = lw.name

        attendance = get_attendance_score(name)
        invalid_ratio = get_invalid_vote_ratio(name)
        adjusted_invalid_score = get_adjusted_invalid_vote_score(name, final_weights["max_invalid_vote_score"])
        vote_match = get_vote_match_ratio(name)
        vote_mismatch = get_vote_mismatch_ratio(name)

        bill_pass_count = get_bill_pass_count(name)
        bill_total = get_bill_total(name)
        bill_ratio = (bill_pass_count / bill_total) if bill_total > 0 else 0

        petition_count = get_petition_count(name)
        petition_pass_count = get_petition_pass_count(name)

        petition_ratio = (petition_count / TOTAL_PETITIONS) if TOTAL_PETITIONS > 0 else 0
        petition_pass_ratio = (petition_pass_count / TOTAL_PASSED_PETITIONS) if TOTAL_PASSED_PETITIONS > 0 else 0

        committee_score, leader_count, secretary_count = get_committee_score(name)

        total_score = (
            (attendance / 100) * final_weights["attendance_weight"] +
            bill_ratio * final_weights["bill_passed_weight"] +
            petition_ratio * final_weights["petition_proposed_weight"] +
            petition_pass_ratio * final_weights["petition_result_weight"] +
            (committee_score / 5) * final_weights["committee_weight"] +  # 5점 만점 기준 정규화
            (adjusted_invalid_score / final_weights["max_invalid_vote_score"]) * final_weights["adjusted_invalid_vote_weight"] +
            (vote_match / 100) * final_weights["vote_match_weight"] +
            ((100 - vote_mismatch) / 100) * final_weights["vote_mismatch_weight"]  # 불일치 비율은 낮을수록 점수 높음
        )

        raw_scores[name] = total_score

        Performance.objects.update_or_create(
            lawmaker=lw,
            defaults={
                "party": party_map.get(name, "무소속"),
                "total_score": 0.0,  # 나중에 정규화 점수로 업데이트
                "attendance_score": attendance,
                "bill_pass_count": bill_pass_count,
                "bill_total": bill_total,
                "petition_count": petition_count,
                "petition_pass_count": petition_pass_count,
                "committee_score": committee_score,
                "committee_leader_count": leader_count,
                "committee_secretary_count": secretary_count,
                "invalid_vote_ratio": invalid_ratio,
                "adjusted_invalid_vote_score": adjusted_invalid_score,
                "vote_match_ratio": vote_match,
                "vote_mismatch_ratio": vote_mismatch,
            }
        )

    normalized = normalize_scores(raw_scores)

    for lw in all_lawmakers:
        Performance.objects.filter(lawmaker=lw).update(total_score=normalized.get(lw.name, 0.0))

    print("✅ 실적 점수 계산 완료 (100점 기준)")

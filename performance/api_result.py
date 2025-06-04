from performance.models import Performance
from vote.models import Lawmaker, LawmakerVoteSummary
from legislation.models import Petition, Member, PetitionIntroducer, CommitteeMember
from attendance.models import Attendance

GAEOL_LIST = ["원안가결", "수정가결", "대안반영가결", "임시가결"]
BUGYEOL_LIST = ["부결", "폐기", "대안반영폐기"]

# 기본 가중치 정의
DEFAULT_WEIGHTS = {
    "attendance_weight": 10.0,
    "bill_passed_weight": 50.0,
    "petition_proposed_weight": 15.5,
    "petition_result_weight": 30.5,
    "committee_weight": 5.0,
    "adjusted_invalid_vote_weight": 1.0,
    "vote_match_weight": 7.5,
    "vote_mismatch_weight": -4.0,
    "max_invalid_vote_score": 2.5,
}

def load_party_info():
    return {member.name: member.party for member in Member.objects.all()}

def get_attendance_score(name):
    record = Attendance.objects.filter(member_name=name).first()
    return round(record.attendance_rate, 2) if record else 0.0

def get_invalid_vote_ratio(name):
    summary = LawmakerVoteSummary.objects.filter(lawmaker__name=name).first()
    return round(summary.invalid_or_abstain_count / summary.total_votes * 100, 2) if summary and summary.total_votes else 0.0

def get_adjusted_invalid_vote_score(ratio, max_score=2.5):
    return round(max_score * (1 - ratio / 100), 2)

def get_vote_match_ratio(name):
    summary = LawmakerVoteSummary.objects.filter(lawmaker__name=name).first()
    if summary:
        total = summary.agree_count + summary.oppose_count
        match = summary.agree_and_passed + summary.oppose_and_failed
        return round(match / total * 100, 2) if total else 0.0
    return 0.0

def get_vote_mismatch_ratio(name):
    summary = LawmakerVoteSummary.objects.filter(lawmaker__name=name).first()
    if summary:
        total = summary.agree_count + summary.oppose_count
        mismatch = summary.agree_and_failed + summary.oppose_and_passed
        return round(mismatch / total * 100, 2) if total else 0.0
    return 0.0

def get_petition_score(name):
    return PetitionIntroducer.objects.filter(introducer_name=name).count()

def get_petition_result_score(name):
    introduced = PetitionIntroducer.objects.filter(introducer_name=name).values_list("petition_id", flat=True)
    return Petition.objects.filter(BILL_ID__in=introduced, PROC_RESULT_CD__in=GAEOL_LIST).count()

def get_committee_score(name):
    member = CommitteeMember.objects.filter(HG_NM=name).first()
    if member:
        if member.JOB_RES_NM == "위원장":
            return 5
        elif member.JOB_RES_NM == "간사":
            return 3
    return 0

def get_bill_pass_score(name):
    summary = LawmakerVoteSummary.objects.filter(lawmaker__name=name).first()
    return summary.agree_and_passed if summary else 0.0

def calculate_performance_scores(**weights):
    # 사용자 입력이 없으면 기본값 사용
    final_weights = {**DEFAULT_WEIGHTS, **weights}

    party_map = load_party_info()
    all_lawmakers = Lawmaker.objects.all()

    for lawmaker in all_lawmakers:
        name = lawmaker.name

        attendance_score = get_attendance_score(name)
        invalid_vote_ratio = get_invalid_vote_ratio(name)
        adjusted_invalid_vote_score = get_adjusted_invalid_vote_score(
            invalid_vote_ratio,
            max_score=final_weights["max_invalid_vote_score"]
        )
        vote_match_ratio = get_vote_match_ratio(name)
        vote_mismatch_ratio = get_vote_mismatch_ratio(name)
        petition_score = get_petition_score(name)
        petition_result_score = get_petition_result_score(name)
        committee_score = get_committee_score(name)
        bill_score = get_bill_pass_score(name)

        total_score = (
            attendance_score * (final_weights["attendance_weight"] / 100) +
            bill_score * final_weights["bill_passed_weight"] +
            petition_score * final_weights["petition_proposed_weight"] +
            petition_result_score * final_weights["petition_result_weight"] +
            committee_score * final_weights["committee_weight"] +
            adjusted_invalid_vote_score * final_weights["adjusted_invalid_vote_weight"] +
            vote_match_ratio * (final_weights["vote_match_weight"] / 100) +
            vote_mismatch_ratio * (final_weights["vote_mismatch_weight"] / 100)
        )

        Performance.objects.update_or_create(
            lawmaker=lawmaker,
            defaults={
                "party": party_map.get(name, "무소속"),
                "total_score": round(total_score, 2),
                "attendance_score": attendance_score,
                "bill_pass_score": bill_score,
                "petition_score": petition_score,
                "petition_result_score": petition_result_score,
                "committee_score": committee_score,
                "invalid_vote_ratio": invalid_vote_ratio,
                "vote_match_ratio": vote_match_ratio,
                "vote_mismatch_ratio": vote_mismatch_ratio,
            }
        )

    print("✅ 실적 계산 완료 (기본 가중치 또는 사용자 입력 반영)")

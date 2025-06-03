from performance.models import Performance
from vote.models import Lawmaker, LawmakerVoteSummary
from legislation.models import Petition, Member, PetitionIntroducer, CommitteeMember
from attendance.models import Attendance  # 🔥 출석 데이터를 가져오기 위해 추가

# 가결 및 부결 유형 정의
GAEOL_LIST = ["원안가결", "수정가결", "대안반영가결", "임시가결"]
BUGYEOL_LIST = ["부결", "폐기", "대안반영폐기"]

def load_party_info():
    """정당 정보 가져오기 (Member 모델에서)"""
    return {member.name: member.party for member in Member.objects.all()}

def get_attendance_score(name):
    """출석 점수 계산 (attendance 앱에서 가져옴)"""
    record = Attendance.objects.filter(member_name=name).first()
    return round(record.attendance_rate, 2) if record else 0.0

def get_invalid_vote_ratio(name):
    """기권/무효 투표 비율 계산"""
    lawmaker_summary = LawmakerVoteSummary.objects.filter(lawmaker__name=name).first()
    return round(lawmaker_summary.invalid_or_abstain_count / lawmaker_summary.total_votes * 100, 2) if lawmaker_summary else 0.0

def get_vote_match_ratio(name):
    """표결 일치 비율 (찬성 가결 + 반대 부결 / 전체 찬반 투표)"""
    lawmaker_summary = LawmakerVoteSummary.objects.filter(lawmaker__name=name).first()
    if lawmaker_summary:
        total_votes = lawmaker_summary.agree_count + lawmaker_summary.oppose_count
        match_votes = lawmaker_summary.agree_and_passed + lawmaker_summary.oppose_and_failed
        return round(match_votes / total_votes * 100, 2) if total_votes else 0.0
    return 0.0

def get_vote_mismatch_ratio(name):
    """표결 불일치 비율 (찬성 부결 + 반대 가결 / 전체 찬반 투표)"""
    lawmaker_summary = LawmakerVoteSummary.objects.filter(lawmaker__name=name).first()
    if lawmaker_summary:
        total_votes = lawmaker_summary.agree_count + lawmaker_summary.oppose_count
        mismatch_votes = lawmaker_summary.agree_and_failed + lawmaker_summary.oppose_and_passed
        return round(mismatch_votes / total_votes * 100, 2) if total_votes else 0.0
    return 0.0

def get_petition_score(name):
    """청원 제시 횟수 계산 (PetitionIntroducer 모델에서 가져옴)"""
    return PetitionIntroducer.objects.filter(introducer_name=name).count()

def get_petition_result_score(name):
    """가결된 청원 개수 계산 (PetitionIntroducer 모델 기반으로 수정)"""
    introduced_petitions = PetitionIntroducer.objects.filter(introducer_name=name).values_list("petition_id", flat=True)
    return Petition.objects.filter(BILL_ID__in=introduced_petitions, PROC_RESULT_CD__in=GAEOL_LIST).count()

def get_committee_score(name):
    """위원회 경력 점수 (위원장 및 간사 여부)"""
    member = CommitteeMember.objects.filter(HG_NM=name).first()  # 🔥 'name' → 'HG_NM'으로 수정

    if member:
        if member.JOB_RES_NM == "위원장":
            return 5  # 위원장은 5점
        elif member.JOB_RES_NM == "간사":
            return 3  # 간사는 3점

    return 0  # 일반 의원은 점수 없음



def get_bill_pass_score(name):
    """법안 가결 점수 계산"""
    lawmaker_summary = LawmakerVoteSummary.objects.filter(lawmaker__name=name).first()
    return lawmaker_summary.agree_and_passed if lawmaker_summary else 0.0

def calculate_performance_scores(
    attendance_weight=-10.0, bill_passed_weight=50.0, petition_proposed_weight=15.5, 
    petition_result_weight=30.5, committee_weight=5.0, invalid_or_abstain_weight=-2.5,
    vote_match_weight=7.5, vote_mismatch_weight=4.0
):
    """전체 성적 계산 및 Django DB에 저장"""
    party_map = load_party_info()
    all_lawmakers = Lawmaker.objects.all()

    for lawmaker in all_lawmakers:
        attendance_score = get_attendance_score(lawmaker.name)
        bill_score = get_bill_pass_score(lawmaker.name)
        petition_score = get_petition_score(lawmaker.name)
        petition_result_score = get_petition_result_score(lawmaker.name)
        committee_score = get_committee_score(lawmaker.name)
        invalid_vote_score = get_invalid_vote_ratio(lawmaker.name)
        vote_match_score = get_vote_match_ratio(lawmaker.name)
        vote_mismatch_score = get_vote_mismatch_ratio(lawmaker.name)

        total_score = (
            attendance_score * attendance_weight +
            bill_score * bill_passed_weight +
            petition_score * petition_proposed_weight +
            petition_result_score * petition_result_weight +
            committee_score * committee_weight +
            invalid_vote_score * invalid_or_abstain_weight +
            vote_match_score * vote_match_weight +
            vote_mismatch_score * vote_mismatch_weight
        )

        Performance.objects.update_or_create(
            lawmaker=lawmaker,
            defaults={
                "party": party_map.get(lawmaker.name, "무소속"),
                "total_score": round(total_score, 2),
                "attendance_score": attendance_score,
                "bill_pass_score": bill_score,
                "petition_score": petition_score,
                "petition_result_score": petition_result_score,
                "committee_score": committee_score,
                "invalid_vote_ratio": invalid_vote_score,
                "vote_match_ratio": vote_match_score,
                "vote_mismatch_ratio": vote_mismatch_score,
            }
        )

    print("🎯 총 실적 점수가 Django DB에 저장되었습니다.")
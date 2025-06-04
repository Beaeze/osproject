from django.db import models
from vote.models import Lawmaker

class Performance(models.Model):
    lawmaker = models.OneToOneField(Lawmaker, on_delete=models.CASCADE)
    party = models.CharField(max_length=100)
    total_score = models.FloatField()
    attendance_score = models.FloatField()
    bill_pass_score = models.FloatField()
    petition_score = models.IntegerField()
    petition_result_score = models.IntegerField()
    committee_score = models.IntegerField()
    invalid_vote_ratio = models.FloatField()
    vote_match_ratio = models.FloatField()
    vote_mismatch_ratio = models.FloatField()

    def __str__(self):
        return f"{self.lawmaker.name} - 실적"
    
class PartyPerformance(models.Model):
    party = models.CharField(max_length=100, unique=True)

    # 출석률 관련 필드
    avg_attendance = models.FloatField(default=0.0)
    max_attendance = models.FloatField(default=0.0)
    min_attendance = models.FloatField(default=0.0)
    std_attendance = models.FloatField(default=0.0)

    # 기권 및 무효표 관련 필드
    avg_invalid_vote_ratio = models.FloatField(default=0.0)
    max_invalid_vote_ratio = models.FloatField(default=0.0)
    min_invalid_vote_ratio = models.FloatField(default=0.0)
    std_invalid_vote_ratio = models.FloatField(default=0.0)

    # 표결 일치율 관련 필드
    avg_vote_match_ratio = models.FloatField(default=0.0)
    max_vote_match_ratio = models.FloatField(default=0.0)
    min_vote_match_ratio = models.FloatField(default=0.0)
    std_vote_match_ratio = models.FloatField(default=0.0)

    # 표결 불일치율 관련 필드
    avg_vote_mismatch_ratio = models.FloatField(default=0.0)
    max_vote_mismatch_ratio = models.FloatField(default=0.0)
    min_vote_mismatch_ratio = models.FloatField(default=0.0)
    std_vote_mismatch_ratio = models.FloatField(default=0.0)

    # 법안 가결 수, 청원 관련 필드
    bill_pass_sum = models.IntegerField(default=0)
    petition_sum = models.IntegerField(default=0)
    petition_pass_sum = models.IntegerField(default=0)

    # 위원회 활동 필드
    committee_leader_count = models.IntegerField(default=0)
    committee_secretary_count = models.IntegerField(default=0)

    # 정당별 총 의원 수
    member_count = models.IntegerField(default=0)

    # 최종 실적 점수 (가중 평균)
    weighted_score = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.party} - 정당 실적"
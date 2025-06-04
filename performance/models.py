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
    avg_attendance = models.FloatField()
    avg_invalid_vote_ratio = models.FloatField()
    avg_vote_match_ratio = models.FloatField()
    avg_vote_mismatch_ratio = models.FloatField()
    bill_pass_sum = models.IntegerField()
    petition_sum = models.IntegerField()
    petition_pass_sum = models.IntegerField()
    committee_leader_count = models.IntegerField()
    member_count = models.IntegerField()
    weighted_score = models.FloatField()

    def __str__(self):
        return f"{self.party} - 정당 실적"
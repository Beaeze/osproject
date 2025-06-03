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
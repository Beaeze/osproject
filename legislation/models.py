from django.db import models

# Create your models here.

class Bill(models.Model):
    AGE = models.CharField(max_length=10)
    BILL_ID = models.CharField(max_length=50, unique=True)
    PROC_RESULT_CD = models.CharField(max_length=20, blank=True)
    PROPOSER = models.CharField(max_length=200, blank=True)
    DETAIL_LINK = models.URLField(blank=True)

    def __str__(self):
        return self.BILL_ID
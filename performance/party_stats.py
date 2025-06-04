import math
from performance.models import Performance, PartyPerformance

def calculate_party_performance():
    performances = Performance.objects.all()
    party_data = {}

    for perf in performances:
        party = perf.party
        if party not in party_data:
            party_data[party] = {
                "attendance": [],
                "invalid_ratio": [],
                "match_ratio": [],
                "mismatch_ratio": [],
                "bill_pass_sum": 0,
                "petition_sum": 0,
                "petition_pass_sum": 0,
                "committee_score": 0,
                "count": 0,
                "score_total": 0,
            }

        p = party_data[party]
        p["attendance"].append(perf.attendance_score)
        p["invalid_ratio"].append(perf.invalid_vote_ratio)
        p["match_ratio"].append(perf.vote_match_ratio)
        p["mismatch_ratio"].append(perf.vote_mismatch_ratio)
        p["bill_pass_sum"] += perf.bill_pass_score
        p["petition_sum"] += perf.petition_score
        p["petition_pass_sum"] += perf.petition_result_score
        p["committee_score"] += perf.committee_score
        p["count"] += 1
        p["score_total"] += perf.total_score

    PartyPerformance.objects.all().delete()

    for party, data in party_data.items():
        avg = lambda x: round(sum(x)/len(x), 2) if x else 0
        weighted_score = round((data["score_total"] / data["count"]) * math.log1p(data["count"]), 2)

        PartyPerformance.objects.create(
            party=party,
            avg_attendance=avg(data["attendance"]),
            avg_invalid_vote_ratio=avg(data["invalid_ratio"]),
            avg_vote_match_ratio=avg(data["match_ratio"]),
            avg_vote_mismatch_ratio=avg(data["mismatch_ratio"]),
            bill_pass_sum=int(data["bill_pass_sum"]),
            petition_sum=int(data["petition_sum"]),
            petition_pass_sum=int(data["petition_pass_sum"]),
            committee_leader_count=data["committee_score"],
            member_count=data["count"],
            weighted_score=weighted_score,
        )

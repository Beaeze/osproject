from django.urls import path
from performance.views import get_performance_data, get_party_weighted_performance

urlpatterns = [
    path("performance-data/", get_performance_data, name="get_performance_data"),
    path("party-weighted-performance/", get_party_weighted_performance, name="get_party_weighted_performance"),
]
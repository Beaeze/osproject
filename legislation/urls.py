from django.urls import path
from legislation.views import (
    get_all_data, get_bill_data, get_committee_member_data,
    get_member_data, get_petition_data
)

urlpatterns = [
    path("all/", get_all_data, name="get_all_data"),
    path("bill/", get_bill_data, name="get_bill_data"),
    path("committee-member/", get_committee_member_data, name="get_committee_member_data"),
    path("member/", get_member_data, name="get_member_data"),
    path("petition/", get_petition_data, name="get_petition_data"),
]
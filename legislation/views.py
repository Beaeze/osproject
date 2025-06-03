from django.shortcuts import render

# Create your views here.
from rest_framework.response import Response
from rest_framework.decorators import api_view
from legislation.models import (
    ALL, Bill, Bill_count, CommitteeMember, Costly, Cost, Etc, Law,
    Member, Petition, PetitionIntroducer, Photo
)
from legislation.serializers import (
    ALLSerializer, BillSerializer, BillCountSerializer, CommitteeMemberSerializer,
    CostlySerializer, CostSerializer, EtcSerializer, LawSerializer,
    MemberSerializer, PetitionSerializer, PetitionIntroducerSerializer, PhotoSerializer
)

@api_view(["GET"])
def get_all_data(request):
    """ALL 모델 데이터 반환"""
    data = ALL.objects.all()
    serializer = ALLSerializer(data, many=True)
    return Response(serializer.data)

@api_view(["GET"])
def get_bill_data(request):
    """Bill 모델 데이터 반환"""
    data = Bill.objects.all()
    serializer = BillSerializer(data, many=True)
    return Response(serializer.data)

@api_view(["GET"])
def get_committee_member_data(request):
    """CommitteeMember 모델 데이터 반환"""
    data = CommitteeMember.objects.all()
    serializer = CommitteeMemberSerializer(data, many=True)
    return Response(serializer.data)

@api_view(["GET"])
def get_member_data(request):
    """Member 모델 데이터 반환"""
    data = Member.objects.all()
    serializer = MemberSerializer(data, many=True)
    return Response(serializer.data)

@api_view(["GET"])
def get_petition_data(request):
    """Petition 모델 데이터 반환"""
    data = Petition.objects.all()
    serializer = PetitionSerializer(data, many=True)
    return Response(serializer.data)
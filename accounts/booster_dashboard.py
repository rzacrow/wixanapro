from .models import User, Alt, Realm, TeamDetail, TeamRequest, Wallet, Transaction, Notifications, Team, InviteMember, RemoveAltRequest, Debt, Loan, CardDetail
from gamesplayed.models import Attendance, CutInIR, AttendanceDetail
from .forms import UpdateProfileForm, CardDetailForm
from gamesplayed.models import CutInIR, Cycle, RunType
from django.db.models import Sum
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

import math

def get_profile(pk) -> str:
    profile = User.objects.filter(id=pk).first()
    profile_form = UpdateProfileForm(initial={'username':profile.username, 'email':profile.email, 'national_code':profile.national_code, 'phone': profile.phone, 'nick_name' : profile.nick_name})

    return profile_form

def get_alts(pk) -> str:
    user = User.objects.get(id=pk)
    alts = Alt.objects.filter(player=user)
    Alt.objects.filter(player=user, status="Rejected").delete()
    return alts

def verified_alts(pk):
    user = User.objects.get(id=pk)
    alts = Alt.objects.filter(player=user, status="Verified")
    return alts

def get_realms():
    realms = Realm.objects.all()
    return realms

def get_team(pk):
    user = User.objects.get(id=pk)
    team_detail = TeamDetail.objects.filter(player=user).first()
    if team_detail:
        team_status = team_detail.team.status
        members = TeamDetail.objects.filter(team=team_detail.team)
        is_leader_team = None
        new_requests = None
        request_count = None
        boosters = None
        if team_detail.team_role == 'Leader' or team_detail.team_role == 'Admin':
            new_requests = TeamRequest.objects.filter(team=team_detail.team, status='Awaiting')
            request_count = TeamRequest.objects.filter(team=team_detail.team, status='Awaiting').count()
            if request_count < 1:
                request_count = None
            boosters = None
            boosters = User.objects.filter(user_type__in=["B", "O", "A"])

            #exlude invite suggestion
            for member in members:
                boosters = boosters.exclude(id=member.player.id)

                
            is_invited = InviteMember.objects.filter(team=team_detail.team)
            if is_invited:
                for member in is_invited:
                    boosters = boosters.exclude(id=member.user.id)
            
            

            is_leader_team = True

        return {'detail': team_detail.team, 'members': members, 'is_leader_team' : is_leader_team, 'new_requests' : new_requests, 'request_count': request_count, 'team_status': team_status, 'boosters': boosters}
    return None


#Get All of attendance
def get_matches(pk):
    user = User.objects.get(id=pk)
    active_attendance = AttendanceDetail.objects.filter(player=user, attendane__cycle__status='O').order_by('-attendane__date_time')[0:10]
    closed_attendance = AttendanceDetail.objects.filter(player=user, attendane__cycle__status='C').order_by('-attendane__date_time')[0:10]
    return {'active_cycle' : active_attendance, 'closed_cycle' : closed_attendance}



def get_card_and_card_form(pk):
    player = User.objects.get(id=pk)
    wallet = Wallet.objects.get_or_create(player=player)
    wallet = wallet[0]
    cards = CardDetail.objects.filter(wallet=wallet)
    card_form = CardDetailForm()
    return {'cards': cards, 'card_form':card_form}



def wallet_report(pk):
    user = User.objects.get(id=pk)
    wallet = Wallet.objects.get_or_create(player=user)
    wallet = wallet[0]

    #wallet balance
    amount = float(wallet.amount)
    if amount >= 1000:
        amount = "{0} K".format(int(amount // 1000))
        
    todays_income = 0
    toweek_income = 0
    tomonth_income = 0

    to_month_attendance = AttendanceDetail.objects.filter(attendane__paid_status=True, player=user, attendane__date_time__month=timezone.datetime.today().month)
    to_day_attendance = AttendanceDetail.objects.filter(attendane__paid_status=True, player=user, attendane__date_time__day=timezone.datetime.today().day)
    last_week = timezone.datetime.now().date() - timedelta(days=7)
    to_week_attendance = AttendanceDetail.objects.filter(Q(attendane__date_time__date__lte=timezone.datetime.now().date()) and Q(attendane__date_time__date__gte=last_week), attendane__paid_status=True, player=user)
    if to_day_attendance:
        todays_income = to_day_attendance.aggregate(Sum('cut', default=0))['cut__sum']
        if todays_income >= 1000:
            todays_income = "{0} K".format(todays_income // 1000)

    if to_week_attendance:
        toweek_income = to_week_attendance.aggregate(Sum('cut', default=0))['cut__sum']
        if toweek_income >= 1000:
            toweek_income = "{0} K".format(toweek_income // 1000)


    if to_month_attendance:
        tomonth_income = to_month_attendance.aggregate(Sum('cut', default=0))['cut__sum']
        if tomonth_income >= 1000:
            tomonth_income = "{0} K".format(tomonth_income // 1000)
    
    return {'amount' : amount, 'todays_income' : todays_income, 'tomonth_income' : tomonth_income, 'toweek_income' : toweek_income}


def cut_per_ir():
    cut_ir = CutInIR.objects.last()
    return cut_ir



def transactions(pk):
    user = User.objects.get(id=pk)
    user_transaction = Transaction.objects.filter(requester=user).order_by('-created')[:10]
    return user_transaction


#Unseen Notificaitons counter
def unseen_notif_badge(pk):
    user = User.objects.get(id=pk)
    count =  Notifications.objects.filter(send_to=user, status='U').count()
    count += InviteMember.objects.filter(user=user).count()
    if user.user_type == 'O':
        count += RemoveAltRequest.objects.filter(status='Awaiting').count()
    if count > 0:
        return count
    else:
        return None    


def attendance_admin():
    attendances = Attendance.objects.filter().order_by('-date_time')
    return attendances
#Get all teams
def get_teams():
    teams = Team.objects.filter(status='Verified')
    return teams

def get_debt(pk):
    try:
        user = User.objects.get(id=pk)
        debts = Debt.objects.get(loan__user=user, paid_status='UnPaid')
        return debts
    except:
        return None
    
def loan_history(pk):
    try:
        user = User.objects.get(id=pk)
        loan_history = Loan.objects.filter(user=user).order_by('-created_at')[0:10]
        return loan_history
    except:
        return None
from django.shortcuts import render, redirect, reverse
from django.views.generic import View
from django.contrib import messages
from django.conf import settings
import requests
from django.contrib.auth import authenticate, login, logout
import shutil, os, random
from . import booster_dashboard
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib.auth.models import Group, Permission
from django.db.models import Q
#forms
from .forms import SignupForm, LoginForm, UpdateProfileForm, CreateTeamForm, CardDetailForm, ResetPasswordForm, ForgetPasswordForm, CheckPasswordForm, LoanForm, DebtForm, TicketForm
from django.contrib.contenttypes.models import ContentType

#models
from .models import User, Wallet, Alt, Realm, Team, TeamDetail, TeamRequest, Notifications, Transaction, InviteMember, RemoveAltRequest, Loan, Debt, WixanaBankDetail, PaymentDebtTrackingCode, Ticket, TicketAnswer, CardDetail
from gamesplayed.models import CutInIR, AttendanceDetail, Attendance

from gamesplayed.forms import DateTimeBootstrap


class Signup(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        
        form = SignupForm()
        
        context = {
            'form' : form
        }

        return render(request, 'accounts/signup.html', context)
    

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        
        form = SignupForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            create_user = User.objects.create(username=data['username'], email=data['email'])
            create_user.set_password(data['password'])
            create_user.save()
            messages.add_message(request, messages.SUCCESS, 'Your account has been successfully created')

            user = authenticate(request, username=data['username'], password=data['password'])
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.add_message(request, messages.SUCCESS, 'Your account was created but there was a problem logging in. Log in to your account')
                return redirect('login')
            
        else:
            return render(request, 'accounts/signup.html', {'form' : form})


class SignupDiscord(View):
    def get(self, request):
        code = request.GET.get('code')
        url = "https://discord.com/api/oauth2/token"
        if code:
            CLIENT_ID = "1187671686179467285"
            CLIENT_SECRET = "tCSBGmtghlEW9Bf15g2hr4PZxR4U0I9g"
            REDIRECT_URI = "https://wixana.ir/signup/discord/response/"

            header = {
                'Content-Type' : 'application/x-www-form-urlencoded'
            }
            data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': REDIRECT_URI
            }

            try:
                response = requests.post(url=f"{url}",headers=header, data=data, auth=(CLIENT_ID, CLIENT_SECRET))
            except:
                messages.add_message(request, messages.ERROR, 'Could not connect to Discord. try again')
                return redirect('signup')
            else:
                user_token = response.json()
                header = {
                    'authorization' : f"{user_token['token_type']} {user_token['access_token']}",
                }

                try:
                    user = requests.get(url="https://discord.com/api/users/@me", headers=header)
                    user = user.json()
                except:
                    messages.add_message(request, messages.WARNING, "Something went wrong!")
                    return redirect('login')
                
                if user['verified'] == True:                    
                    #get user avatar with discord cdn
                    avatar_hash = None

                    if user['avatar']:
                        try:
                            r = requests.get(url=f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}", stream=True)
                            img_path = f"media/profile/discord/{user['id']}/"
                            #make top directories
                            os.makedirs(os.path.dirname(img_path), exist_ok=True)

                            #get image from request and copy into follow path with unique user_id/user_avatar_hash
                            with open("{0}{1}.png".format(img_path, user['avatar']), 'wb') as f:
                                shutil.copyfileobj(r.raw, f)

                                #save path profile into db
                                avatar_hash = "{0}{1}.png".format(img_path, user['avatar'])
                        except:
                            messages.add_message(request, messages.WARNING, "There was a problem getting your profile picture from Discord")

                    #if username exist
                    if User.objects.filter(username=user['username']).exists():
                        get_user = User.objects.get(username=user['username'])
                        if get_user.discord_id:
                            get_user.email = user['email']
                            get_user.discord_id = user['id']
                            get_user.avatar_hash = avatar_hash
                            get_user.save()
                            login(request, get_user, backend=settings.AUTHENTICATION_BACKENDS[0])
                            messages.add_message(request, messages.SUCCESS, message=f"Welcome back {user['username']}")
                            return redirect('dashboard')
                        else:
                            messages.add_message(request, messages.ERROR, "This username is reserved. You can't connect to it with Discord")
                            return redirect('login')
                    
                    #if email exist
                    if User.objects.filter(email=user['email']).exists():
                        get_user = User.objects.get(email=user['email'])
                        #check user sign in from discord : if True -> change username
                        if get_user.discord_id:
                            if get_user.discord_id == user['id']:
                                get_user.username = user['username']
                                get_user.discord_id = user['id']
                                get_user.avatar_hash = avatar_hash
                                get_user.save()
                                login(request, get_user, backend=settings.AUTHENTICATION_BACKENDS[0])
                                messages.add_message(request, messages.SUCCESS, message=f"Welcome back {user['username']}")
                                return redirect('dashboard')
                            else:
                                messages.add_message(request, messages.ERROR, "This email is reserved. You can't connect to it with Discord")
                                return redirect('login')
                        else:
                                messages.add_message(request, messages.ERROR, "This email is reserved. You can't connect to it with Discord")
                                return redirect('login')            
                            


                    create_user = User.objects.create(username=user['username'], email=user['email'], discord_id=user['id'], avatar_hash=avatar_hash)
                    create_user.save()
                    login(request, create_user, backend=settings.AUTHENTICATION_BACKENDS[0])
                    messages.add_message(request, messages.SUCCESS, 'Your account has been successfully created')
                    return redirect('dashboard')

                else:
                    messages.add_message(request, messages.ERROR, 'Your Discord account has not been verified')
                    return redirect('signup')              
        else:
            messages.add_message(request, messages.ERROR, 'There was a problem authenticating you through Discord')
            return redirect('signup')


class Login(View):
    def get(self,request):
        #if user was logged in, then redirect to dashboard
        if request.user.is_authenticated:
            return redirect('dashboard')
        
        form = LoginForm()

        context = {
            'form' : form,
        }

        return render(request, 'accounts/login.html', context)
    
    def post(self, request):
        form = LoginForm(request.POST)

        if form.is_valid():
            #get cleaned data
            data = form.cleaned_data
            password = data['password']
            username = data['username']
            #If a user with the entered profile is found
            user = authenticate(request, username=username,password=password)
            if user is not None:
                login(request, user)
                messages.add_message(request, level=messages.SUCCESS, message=f"Welcome back {username}")
                return redirect('dashboard')
            else:
                messages.add_message(request, level=messages.ERROR, message='Wrong username or password')
                return redirect('login')
        else:
            context = {
                'form': form
            }
            return render(request, 'accounts/login.html', context)
        

class Logout(View):
    def get(self, request):
        logout(request)
        return redirect('login')
    
    
class Dashboard(View):
    def get(self, request):
        if request.user.is_authenticated:
            
            #Define Context
            context = dict()

            #get user 
            user = request.user
            #get user profile
            context['profile_form'] = booster_dashboard.get_profile(pk=user.id)

            #if get query for add alts exist
            altname =  request.GET.get('altname')
            realm = request.GET.get('realm')

            payment_character = request.GET.get('payment_character')
            #A flag to identify the user level
            is_superuser = None
            is_user = None
            remove_alt_request = None
            has_perm_view_attendance_admin = None


            if altname and realm:
                if (altname == '') or (altname == None) or (int(realm) == 0):
                    messages.add_message(request, messages.ERROR, 'You must fill all required fields')
                else:
                    realm_obj = Realm.objects.get(id=realm)
                    Alt.objects.create(realm=realm_obj, name=altname, player=request.user)
                    messages.add_message(request, messages.SUCCESS, 'Alt added successfully, after admin approval, it will be placed in your profile')


            tab = request.GET.get('tab')
            if tab:
                context['tab'] = tab


            if payment_character:
                if payment_character != 0:
                    at_id = request.GET.get('at_pk')
                    at_ad = AttendanceDetail.objects.get(id=at_id)
                    alt = Alt.objects.get(id=payment_character)
                    at_ad.payment_character = alt
                    at_ad.save()
                    return redirect(reverse('dashboard') + '?tab=attendance')




            if user.is_superuser:
                remove_alt_request = RemoveAltRequest.objects.filter(status='Awaiting')
                context['remove_alt_request'] = remove_alt_request
                #change user type to Owner in first login
                is_superuser = True
                if user.user_type != 'O':
                    user.user_type = 'O'
                    user.save()
                    return redirect('dashboard')
                
            if user.user_type != 'U':
                context['alts'] = booster_dashboard.get_alts(pk=user.id)
                context['realms'] = booster_dashboard.get_realms()
                context['team'] = booster_dashboard.get_team(pk=user.id)
                context['create_team_form'] = CreateTeamForm()
                context['matches'] = booster_dashboard.get_matches(pk=user.id)
                context['card_detail'] = booster_dashboard.get_card_and_card_form(pk=user.id)
                context['wallet_report'] = booster_dashboard.wallet_report(pk=user.id)
                context['cut_per_ir'] = booster_dashboard.cut_per_ir()
                context['transactions'] = booster_dashboard.transactions(pk=user.id)
                context['unseen_notif_count'] = booster_dashboard.unseen_notif_badge(pk=user.id)
                context['teams'] = booster_dashboard.get_teams()

                context['verified_alts'] = booster_dashboard.verified_alts(pk=user.id)
                context['loan_form'] = LoanForm()
                context['debt_form'] = DebtForm()
                context['loan_history'] = booster_dashboard.loan_history(pk=user.id)
                context['debts'] = booster_dashboard.get_debt(pk=user.id)

                if (user.is_staff) and (user.has_perm('gamesplayed.add_attendance')):
                    has_perm_view_attendance_admin = True
                    context['admin_attendances'] = booster_dashboard.attendance_admin()

                try:
                    context['wixana_card_detail'] = WixanaBankDetail.objects.last()
                except:
                    context['wixana_card_detail'] = None

            else:
                is_user = True
                context['is_user'] = is_user

            context['notifications'] = Notifications.objects.filter(send_to=request.user, status="U").order_by('-created_at')
            context['notifications_history'] = Notifications.objects.filter(send_to=request.user, status="S").order_by('-created_at')[0:10]
            context['invite_request'] = InviteMember.objects.filter(user=user)
            context['ticket_form'] = TicketForm()
            context['tickets_history'] = Ticket.objects.filter(user=user).order_by('-created')[0:10]
            context['tickets_answered'] = TicketAnswer.objects.filter(ticket__user=user)

            
            context['is_superuser'] = is_superuser
            context['has_perm_view_attendance_admin'] = has_perm_view_attendance_admin
            return render(request, 'accounts/dashboard.html', context)
        else:
            messages.add_message(request, messages.WARNING, 'Login required!')
            return redirect('login')
        

    def post(self, request):
        profile_form = UpdateProfileForm(request.POST, request.FILES)
        if profile_form.is_valid():
            user = User.objects.get(id=request.user.id)
            data = profile_form.cleaned_data
            username = data['username']
            email = data['email']
            national_code = data['national_code']
            nick_name = data['nick_name']
            phone = data['phone']

            try:
                user.avatar = request.FILES['avatar']
            except:
                pass

            if user.discord_id:
                if (username != user.username) or (email != user.email):
                    messages.add_message(request, messages.WARNING, "You are not allowed to change your username or email")
                    user.save()
                    return redirect('dashboard')

            
            username_exist = User.objects.filter(username=username)
            if username_exist.exists():
                if (username_exist.exclude(username=user.username)):
                    messages.add_message(request, messages.WARNING, "Another account is using this username")
                    user.save()
                    return redirect('dashboard')

            email_exist = User.objects.filter(email=email)
            if email_exist.exists():
                if (email_exist.exclude(email=user.email)):
                    messages.add_message(request, messages.WARNING, "Another account is using this email")
                    user.save()
                    return redirect('dashboard')

            user.username = username
            user.email = email
            user.national_code = national_code
            user.phone = phone
            user.nick_name = nick_name
            user.save()

            gp = Group.objects.get_or_create(name="COMPLETED_PROFILE")
            ct_team = ContentType.objects.get_for_model(Team)
            ct_loan = ContentType.objects.get_for_model(Loan)
            ct_transaction = ContentType.objects.get_for_model(Transaction)
            perms = Permission.objects.filter(Q(content_type=ct_team) | Q(content_type=ct_loan) | Q(content_type=ct_transaction))

            if ((user.phone is not None) and (user.phone != "")) and ((user.national_code is not None) and (user.national_code != "")) and ((user.email is not None) and (user.email != "")):
                gp[0].permissions.set(perms)
                gp[0].save()
                user.groups.add(gp[0]) 
                user.save()
            else:
                user.groups.remove(gp[0]) 
                user.save()

            messages.add_message(request, messages.SUCCESS, "Profile updated successfully")
            return redirect('dashboard')
        
        else:
            messages.add_message(request, messages.WARNING, profile_form.errors)
            return redirect('dashboard')


class CreateTeam(View):
    def post(self, request):
        user = request.user
        if user.is_authenticated and user.has_perm('accounts.add_team'):
            create_team_form = CreateTeamForm(request.POST)
            if create_team_form.is_valid():
                data = create_team_form.cleaned_data
                team = Team.objects.create(name=data['name'])
                team.save()

                TeamDetail.objects.create(team=team, player=request.user, team_role="Leader")
                messages.add_message(request, messages.SUCCESS, 'Your team created successfully')
            else:
                messages.add_message(request, messages.ERROR, f"Error team form: name is required")
        else:
            messages.add_message(request, messages.ERROR, "You do not have permission to do this. Please complete your profile")

        return redirect(reverse('dashboard') + '?tab=team')

class LeftTheTeam(View):
    def get(self, request, team_pk):
        team = Team.objects.filter(id=team_pk).first()
        team_detail = TeamDetail.objects.filter(team=team, player=request.user).first()
        if team_detail:
            is_leader = False
            if team_detail.team_role == "Leader":
                is_leader = True

            team_detail.delete()
            messages.add_message(request, messages.SUCCESS, f"You left team {team.name}")
            if (TeamDetail.objects.filter(team=team).count()) < 1:
                #if members of team equal to 0, removed the team 
                team.delete()
            elif is_leader:
                #change leader team
                next_leader = TeamDetail.objects.filter(team=team).first()
                next_leader.team_role = "Leader"
                next_leader.save()

            return redirect(reverse('dashboard') + '?tab=team')
        else:
            messages.add_message(request, messages.ERROR, f"Request is not valid")
            return redirect(reverse('dashboard') + '?tab=team')


class TeamDetailLink(View):
    def get(self, request, team_pk):
        if request.user.is_authenticated:
            if request.user.user_type == 'U':
                messages.add_message(request, messages.WARNING, 'You are not allowed to see this content')
                return redirect('dashboard')
            
            team = Team.objects.filter(id=team_pk).first()
            if team:
                if team.status != 'Verified':
                    messages.add_message(request, messages.WARNING, 'Team not found')
                    return redirect('dashboard')
                
                user_have_team = None
                user = request.user
                td = TeamDetail.objects.filter(player=user)
                members = TeamDetail.objects.filter(team=team)
                if td:
                    user_have_team = True
            else:
                messages.add_message(request, messages.WARNING, 'Team not found')
                return redirect('dashboard')
            

            context = {
                'team' : team,
                'user_have_team' : user_have_team,
                'members' : members,
                'count' : members.count(),
            }

            return render(request, 'accounts/team.html', context)
        else:
            messages.add_message(request, messages.WARNING, 'Login required!')
            return redirect('login')
    
    def post(self, request, team_name, team_pk):
        user_requested = request.user
        if user_requested.user_type != 'U':
            team = Team.objects.filter(id=team_pk).first()
            is_requesetd_before = TeamRequest.objects.filter(player=user_requested, team=team, status='Awaiting')
            if not is_requesetd_before:
                TeamRequest.objects.create(player=user_requested, team=team)
                messages.add_message(request, messages.SUCCESS, 'Your request to join the team has been sent')
            else:
                messages.add_message(request, messages.ERROR, 'You have already sent a request to this team')
            return redirect(reverse('dashboard') + '?tab=team')
        else:
            messages.add_message(request, messages.ERROR, 'You are not allowed to join the team')
            return redirect(reverse('dashboard') + '?tab=team')
    

class RemoveTeamMember(View):
    def get(self, request, team_pk, member_pk):
        leaders = TeamDetail.objects.filter(team__id=team_pk, team_role='Leader')
        is_leader = False
        for leader in leaders:
            if request.user == leader.player:
                is_leader = True
                break
        
        if is_leader:
            member = TeamDetail.objects.get(team__id=team_pk, id=member_pk)
            user = member.player
            team = member.team
            member.delete()
            messages.add_message(request, messages.SUCCESS, f'User {user.username} has been removed from your team')
            Notifications.objects.create(send_to=user, title=f"{team.name} Team", caption="You have been removed")
            return redirect(reverse('dashboard') + '?tab=team')
        else:
            messages.add_message(request, messages.ERROR, f'Request is not valid')
            return redirect(reverse('dashboard') + '?tab=team')


class JoinTeamResponse(View):
    def post(self, request):
        data = request.POST['response']
        team_id = request.POST['team']
        username = request.POST['username']
        team = Team.objects.filter(id=team_id).first()
        player = User.objects.filter(username=username).first()

        if data == 'accept':
            if not TeamDetail.objects.filter(player=player):
                TeamDetail.objects.create(team=team, player=player)
                Notifications.objects.create(send_to=player, title="Join Team", caption=f"You are now a member of {team.name}")
                messages.add_message(request, messages.SUCCESS, message=f"User {player.username} joined to your team")
            else:
                Notifications.objects.create(send_to=player, title="Join Team", caption=f"Your request to joined team {team.name} accepted, but you are already have a team")
                messages.add_message(request, messages.WARNING, message=f"User {player.username} already has a team")
            try:
                rq = TeamRequest.objects.filter(team=team, player=player, status="Awaiting").first()
                rq.status = "Verified"
                rq.save()
                del rq
            except:
                pass
            return redirect(reverse('dashboard') + '?tab=team')
        else:
                Notifications.objects.create(send_to=player, title="Join Team", caption=f"Your request to joined team {team.name} rejected.")
                messages.add_message(request, messages.WARNING, message=f"User {player.username} rejected!")
                rq = TeamRequest.objects.filter(team=team, player=player, status="Awaiting").first()
                rq.status = "Rejected"
                rq.save()
                del rq

                
                return redirect(reverse('dashboard') + '?tab=team')
        
class SeenNotif(View):
    def get(self, request):
        if request.user.is_authenticated:
            notif = Notifications.objects.filter(send_to=request.user)
            for nf in notif:
                nf.status = 'S'
                nf.save()
            
        return redirect(reverse('dashboard') + '?tab=notifications')


class CardUpdateDetail(View):
    def post(self, request):
        user = request.user

        if user.is_authenticated and user.has_perm('accounts.add_carddetail'):
            card_detail_form = CardDetailForm(request.POST)
            if card_detail_form.is_valid():
                data = card_detail_form.cleaned_data
                try:
                    wallet = Wallet.objects.get(player=request.user)
                    card = CardDetail.objects.create(wallet=wallet, card_number=data['card_number'], full_name=data['full_name'], shaba=data['shaba'])
                    card.save()
                    messages.add_message(request, messages.SUCCESS, 'Wallet detail, updated successfully')
                    return redirect(reverse('dashboard') + '?tab=wallet')
                except:
                    messages.add_message(request, messages.ERROR, message="something went wrong!")
                    return redirect(reverse('dashboard') + '?tab=wallet')
            else:
                messages.add_message(request, messages.ERROR, card_detail_form.errors)
        else:
            messages.add_message(request, messages.ERROR, "You do not have permission to do this. Please complete your profile")

        return redirect(reverse('dashboard') + '?tab=wallet')
        

class AskingMoney(View):
    def post(self, request):
        if request.user.is_authenticated:
            user = request.user
            if user.user_type != 'U' and user.has_perm('accounts.add_transaction'):
                currency = request.POST['asking_money_type']
                amount = int(request.POST['asking_money_amount'])
                wallet = Wallet.objects.get(player=user)
                card_detail = request.POST['card']

                amount = amount * 1000
                if (amount <= wallet.amount) and (wallet.amount >= 1000):
                    if amount >= 1:
                        to_day_request = Transaction.objects.filter(requester=user, created__day=timezone.datetime.today().day).count()
                        if to_day_request >= 2:
                            messages.add_message(request, messages.WARNING, "You can payment request twice a day")
                            return redirect(reverse('dashboard') + '?tab=wallet')
                        
                        wallet.amount -= amount
                        wallet.save()
                        amount = amount // 1000
                        if currency == 'IR':
                            try:
                                try:
                                    card_detail = CardDetail.objects.get(id=card_detail)
                                except:
                                    card_detail = None
                                    messages.add_message(request, messages.ERROR, 'Card number is not valid')
                                    wallet.amount += (amount * 1000)
                                    wallet.save()
                                    return redirect(reverse('dashboard') + "?tab=wallet")

                                cut_in_ir = CutInIR.objects.last()
                                cut_in_ir = int(cut_in_ir.amount)
                            except:
                                messages.add_message(request, messages.ERROR, 'There was a problem receiving the amount in Tomans, try again later')
                                wallet.amount += (amount * 1000)
                                wallet.save()
                                return redirect(reverse('dashboard') + "?tab=wallet")
                            else:
                                amount_in_ir = amount * cut_in_ir
                                Transaction.objects.create(requester=user, amount=amount_in_ir, currency=currency, caption=f"Cut: {amount} K", card_detail=card_detail)
                            messages.add_message(request, messages.SUCCESS, "Your payment request has been successfully registered")
                        else:
                            try:
                                alt_id = request.POST['alt']  
                                alt = Alt.objects.get(id=alt_id)
                            except:
                                wallet.amount += (amount * 1000)
                                wallet.save()
                                messages.add_message(request, messages.WARNING, 'Alt is not valid')
                                return redirect(reverse('dashboard') + '?tab=wallet')

                            Transaction.objects.create(requester=user, amount=amount, currency=currency, alt=alt)
                            messages.add_message(request, messages.SUCCESS, "Your payment request has been successfully registered")
                        admins = User.objects.filter(user_type__in=['A', 'O'])
                        for admin in admins:
                            Notifications.objects.create(send_to=admin, title="Payment reqeust", caption=f"You have a new payment request from {request.user.username}")
                    else:
                        messages.add_message(request, messages.WARNING, 'Payment request in not valid')

                else:
                    messages.add_message(request, messages.WARNING, 'Your wallet balance is not enough')
            else:
                messages.add_message(request, messages.ERROR, "You do not have permission to do this. Please complete your profile")
            
        return redirect(reverse('dashboard') + '?tab=wallet')
    

class ForgetPassword(View):
    def get(self, request):
        form = ForgetPasswordForm()

        context = {
            'form' : form,
        }

        return render(request, 'accounts/forgetpassword.html', context)
    
    def post(self, request):
        form = ForgetPasswordForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            email = data['email']

            user = User.objects.filter(email=email)

            if user:
                user = User.objects.filter(email=email).first()
                if user.discord_id:
                    messages.add_message(request, messages.WARNING, "You are logged in with Discord, you cannot change your password")
                    return redirect('login')
                
                numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
                confirm_code = ''
                for i in range(6):
                    confirm_code += random.choice(numbers)

                request.session['confirm_code'] = confirm_code
                request.session['email_address'] = data['email']

                subject = 'Wixana | Authentication'
                message = f'Confirm code: {confirm_code} \n\n If this request is not from your side, inform the support through a ticket.\n\n === WIXANA ==='
                email_from = settings.EMAIL_HOST_USER
                email_to = [data['email']]

                try:
                    send_mail(subject, message, email_from, email_to)
                except:
                    messages.add_message(request, messages.WARNING, 'Something went wrong! please try again')
                    return redirect('forgetpassword')
                return redirect('checkpassword')

            else:
                messages.add_message(request, messages.WARNING, 'No account found with this email')
                return redirect('forgetpassword')
        else:
            context = {
                'form' : form
            }
            return render(request, 'accounts/forgetpassword.html', context)


class CheckPassword(View):
    def get(self, request):
        if request.session['confirm_code']:
            form = CheckPasswordForm()

            context = {
                'form' : form,
            }

            return render(request, 'accounts/checkpassword.html', context)
        else:
            return redirect('forgetpassword')
    
    def post(self, request):
        form = CheckPasswordForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            if request.session['confirm_code'] == data['check_code']:
                del request.session['confirm_code']

                return redirect('resetpassword')
            else:
                context = {
                    'form' : form,
                }
                messages.add_message(request, messages.ERROR, 'Code is not valid')
                return render(request, 'accounts/checkpassword.html', context)
        else:
            context = {
                'form' : form
            }
            return render(request, 'accounts/checkpassword.html', context)
        

class ResetPassword(View):
    def get(self, request):
        try:
            form = ResetPasswordForm()
            context = {
                'form' : form,
            }
            return render(request, 'accounts/resetpassword.html', context)
        except:
            return redirect('forgetpassword')
    
    def post(self, request):
        form = ResetPasswordForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            try:
                email = request.session['email_address']
                user = User.objects.get(email = email)
                user.set_password(data['password'])
                user.save()
                del request.session['email_address']
                messages.add_message(request, messages.SUCCESS, 'Your password changed successfully, Enter it now!')
                return redirect('login')
            except:
                messages.add_message(request, messages.WARNING, 'There was a problem in reset password, try again')
                return redirect('forgetpassword')
        else:
            context = {
                 'form' : form,
            }
            return render(request, 'accounts/resetpassword.html', context)


class InviteUser(View):
    def post(self, request, team_pk):
        try:
            team = Team.objects.get(id=team_pk)
            #If team not verified
            if team.status != "Verified":
                messages.add_message(request, messages.WARNING, f"Your team is not verified")
                return redirect(reverse('dashboard') + '?tab=team')
            
            user_ids = list()
            for key in request.POST:
                if 'user_' in key:
                    user_ids.append(request.POST[key])
            for user_pk in user_ids:
                try:
                    user = User.objects.get(id=user_pk)
                    InviteMember.objects.create(team=team, user=user, answer='Pending')
                except:
                    continue

            messages.add_message(request, messages.SUCCESS, f"The invite request has been sent")
            return redirect(reverse('dashboard') + '?tab=team')
        except:
            messages.add_message(request, messages.WARNING, f"There was problem to send invitation request, Try again")
            return redirect(reverse('dashboard') + '?tab=team')

class InviteUserResponse(View):
    def get(self, request, team_pk, user_pk, response):
        try:
            user = User.objects.get(id=user_pk)
            team = Team.objects.get(id=team_pk)
            answer = response

            if answer == "Accept":
                if not TeamDetail.objects.filter(player=user):
                    TeamDetail.objects.create(team=team, player=user)
                    tds = TeamDetail.objects.filter(team=team, team_role='Leader')
                    for td in tds:
                        Notifications.objects.create(send_to=td.player, title="Join Team", caption=f"User {user.username} joined to your team")
                else:
                    messages.add_message(request, messages.WARNING, message=f"you are already have a team")
                im = InviteMember.objects.get(team=team, user=user)
                im.delete()
                return redirect(reverse('dashboard') + '?tab=team')
            elif answer == 'Reject':
                im = InviteMember.objects.get(team=team, user=user)
                im.delete()

                messages.add_message(request, messages.WARNING, f"Resault was recorded")
                return redirect(reverse('dashboard') + '?tab=notifications')
            else:
                messages.add_message(request, messages.WARNING, f"Request is not valid")
                return redirect(reverse('dashboard') + '?tab=notifications')
        except:
            messages.add_message(request, messages.WARNING, f"Request is not valid")
            return redirect(reverse('dashboard') + '?tab=notifications')


class PositionMemberTeam(View):
    def get(self, request, team_pk, user_pk):
        leaders = TeamDetail.objects.filter(team__id=team_pk, team_role='Leader')
        is_leader = False
        for leader in leaders:
            if request.user == leader.player:
                is_leader = True
                break
        
        if is_leader:
            td = TeamDetail.objects.filter(id=user_pk).first()
            if request.GET['pos'] == 'admin':
                td.team_role = 'Admin'
            elif request.GET['pos'] == 'leader':
                team = td.team 
                leader = TeamDetail.objects.filter(team=team, team_role='Leader').first()   
                leader.team_role = 'Admin'
                leader.save()
                td.team_role = 'Leader'
            elif request.GET['pos'] == 'member':
                td.team_role = 'Member'
            
            td.save()
            messages.add_message(request, messages.SUCCESS, message=f'User {td.player.username} changed to {td.team_role}')
            Notifications.objects.create(send_to=td.player, title="Change in the team", caption=f"Your role in the team was changed to {td.team_role}")
            return redirect(reverse('dashboard') + '?tab=team')
        else:
            messages.add_message(request, messages.ERROR, 'Request is not valid')
            return redirect(reverse('dashboard') + '?tab=team')
        

class RemoveAlts(View):
    def get(self, request, pk):
        admins = User.objects.filter(user_type='O')
        alt = Alt.objects.filter(id=pk).first()
        if alt.player == request.user:
            for admin in admins:
                RemoveAltRequest.objects.create(alt=alt, user=alt.player, status='Awaiting')
                messages.add_message(request, messages.SUCCESS, 'Your request has been registered. After checking the admin, the result will be sent to you')
                return redirect('dashboard')
        else:
            messages.add_message(request, messages.ERROR, 'Request is not valid')
            return redirect('dashboard')
        

class RemoveAltsResponse(View):
    def get(self, request, pk):
        admins = User.objects.filter(user_type='O')
        if request.user in admins:
            try:
                rq = RemoveAltRequest.objects.get(id=pk)
                ans = request.GET['answer']
                if ans == 'no':
                    Notifications.objects.create(send_to=rq.user, title='Delete alt request', caption='Your request rejected by admin')
                    rq.delete()
                    messages.add_message(request, messages.SUCCESS, 'Changes saved successfully')
                    return redirect(reverse('dashboard') + '?tab=notifications')
                elif ans == 'yes':
                    Notifications.objects.create(send_to=rq.user, title='Delete alt request', caption=f'{rq.alt.name} alt has been deleted!')
                    Alt.objects.get(id=rq.alt.id).delete()
                    rq.delete()
                    messages.add_message(request, messages.SUCCESS, 'Changes saved successfully')
                    return redirect(reverse('dashboard') + '?tab=notifications')             
            except:
                messages.add_message(request, messages.WARNING, 'Something went wrong!')
                return redirect(reverse('dashboard') + '?tab=notifications')
            
        else:
            messages.add_message(request, messages.ERROR, 'Your request is not valid')
            return redirect(reverse('dashboard') + '?tab=notifications')


class LoanApplication(View):
    def post(self, request):
        user = request.user

        if user.is_authenticated and user.has_perm('accounts.add_loan'):
            debts = Debt.objects.filter(loan__user=request.user, paid_status='Unpaid')
            loans = Loan.objects.filter(user=request.user, loan_status='Pending')
            #if user have an unpaid loan
            if debts:
                messages.add_message(request, messages.WARNING, 'You have an unpaid loan')
                return redirect(reverse('dashboard') + '?tab=loan')
                    
            if loans:
                messages.add_message(request, messages.WARNING, 'You have an unchecked loan request')
                return redirect(reverse('dashboard') + '?tab=loan')        
            
            

            form = LoanForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                try:
                    alt = Alt.objects.get(id=form.data['alt'])
                    note = data['note']
                    
                    Loan.objects.create(alt=alt, note=note, amount=data['amount'], user=request.user)
                    messages.add_message(request, messages.SUCCESS, 'Your request for a loan has been registered')
                    admins = User.objects.filter(user_type='O')
                    requester_name = request.user.username
                    if request.user.nick_name:
                        requester_name = request.user.nick_name

                    for admin in admins:
                        Notifications.objects.create(send_to=admin, title='New Loan Request', caption=f"You have a new loan request with the amount of {data['amount']} K from user {requester_name}")
                    return redirect(reverse('dashboard') + '?tab=loan')
                except:
                    messages.add_message(request, messages.WARNING, 'Your request is not valid')
                    return redirect(reverse('dashboard') + '?tab=loan')
            else:
                messages.add_message(request, messages.WARNING, 'Your request is not valid')
        else:
            messages.add_message(request, messages.ERROR, "You do not have permission to do this. Please complete your profile")

        return redirect(reverse('dashboard') + '?tab=loan')


class DebtPaymentFromWallet(View):
    def post(self, request):
        try:
            method = request.GET['method']
            if method == 'wallet':
                debt = Debt.objects.get(id=request.POST['debt_id'])
                amount = debt.debt_amount * 1000
                wallet = Wallet.objects.get(player=debt.loan.user)

                #if wallet balance is insufficient
                if amount > wallet.amount:
                    messages.add_message(request, messages.WARNING, 'Your account balance is insufficient')
                    return redirect(reverse('dashboard') + '?tab=loan')
                
                debt.paid_status = 'Paid'
                debt.debt_amount = 0
                debt.save()
                wallet.amount -= amount
                wallet.save()
                Notifications.objects.create(send_to=debt.loan.user, title="Payment receipts", caption="Your debt has been settled")
                admins = User.objects.filter(user_type='O')
                name = debt.loan.user.username
                if debt.loan.user.nick_name:
                    name = debt.loan.user.nick_name
                for admin in admins:
                    Notifications.objects.create(send_to=admin, title='Debt deposit', caption=f"User {name} paid debt with {amount // 1000} K amount via wallet")
                return redirect(reverse('dashboard') + '?tab=loan')
            

            elif method == 'tracking_code':
                amount = request.POST['debt_in_ir']
                debt = Debt.objects.get(id=request.POST['debt_id'])
                tracking_code = request.POST['tracking_code']

                #if tracking code is not valid
                if (tracking_code == None) or (len(tracking_code) < 1) or (not tracking_code.isdigit()):
                    messages.add_message(request, messages.WARNING, 'Your request is not valid')
                    return redirect(reverse('dashboard') + '?tab=loan')
                                
                PaymentDebtTrackingCode.objects.create(debt_amount_IR=amount, debt=debt, tracking_code=tracking_code)
                messages.add_message(request, messages.SUCCESS, 'Your request has been registered. After checking the admin, the result will be announced')
                admins = User.objects.filter(user_type='O')
                for admin in admins:
                    Notifications.objects.create(send_to=admin, title='Debt deposit', caption="You have an unchecked payment via tracking code. See it from the admin panel")
                return redirect(reverse('dashboard') + '?tab=loan')
        except:
            messages.add_message(request, messages.WARNING, 'Your request is not valid')
            return redirect(reverse('dashboard') + '?tab=loan')      


class SubmitTicket(View):
    def post(self, request):
        form = TicketForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            Ticket.objects.create(user=request.user, title=data['title'], text=data['text'])
            messages.add_message(request, messages.SUCCESS, 'Ticket was sent successfully')
            return redirect(reverse('dashboard') + '?tab=ticket')
        else:
            messages.add_message(request, messages.WARNING, 'Request is not valid')
            return redirect(reverse('dashboard') + '?tab=ticket')
        

class DeleteBankCard(View):
    def get(self, request, pk):
        try:
            card_detail = CardDetail.objects.get(id=pk)
            if request.user == card_detail.wallet.player:
                card_detail.delete()
                messages.add_message(request, messages.SUCCESS, 'Delete card successfully')
                return redirect(reverse('dashboard') + "?tab=wallet")
        except:
                messages.add_message(request, messages.SUCCESS, 'Something went wrong!')
                return redirect(reverse('dashboard') + "?tab=wallet")

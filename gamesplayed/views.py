from django.shortcuts import render, redirect, reverse, HttpResponse, HttpResponseRedirect
from django.views.generic import View
from django.contrib import messages
from .models import Attendance, AttendanceDetail, Cycle, RunType, Realm, Role, SpecificTime, Guild, CutDistributaion, CurrentRealm
from .forms import DateTimeBootstrap
from django.utils import timezone
from accounts.models import User, Alt, Team, TeamDetail
import datetime
import json

class ViewAttendance(View):
    def get(self, request, pk):
        if request.user.is_authenticated:
            if request.user.is_staff:
                try:
                    attendance = Attendance.objects.get(id=pk)
                    guild = Guild.objects.get(attendance=attendance)
                    cut_dist = CutDistributaion.objects.get(attendance=attendance)
                    a_detail = AttendanceDetail.objects.filter(attendane=attendance)
                    current_realm = CurrentRealm.objects.filter(attendance=attendance)
                    realms_count = 0
                    if not current_realm:
                        current_realm = None
                    else:
                        realms_count = current_realm.count()

                    cycles = Cycle.objects.filter(status="O")
                    run_types = RunType.objects.filter()
                    date_time_form = DateTimeBootstrap(initial={'date_time': timezone.datetime.now()})
                    realms = Realm.objects.filter()
                    boosters = User.objects.filter(user_type__in=['O','A', 'B'])
                    alts = Alt.objects.filter(status="Verified")
                    roles = Role.objects.filter()
                    teams = Team.objects.filter()
                    specific_time = SpecificTime.objects.filter()
                    team_detail = TeamDetail.objects.filter()



                    context = {
                        'cycles' : cycles,
                        'run_types' : run_types,
                        'date_time_picker' : date_time_form,
                        'realms' : realms,
                        'boosters' : boosters,
                        'alts' : alts,
                        'roles' : roles,
                        'teams' : teams,
                        'specific_time' : specific_time,
                        'team_detail' : team_detail,
                        'attendance' : attendance,
                        'guild' : guild,
                        'cut_dist' : cut_dist,
                        'a_detail' : a_detail,
                        'current_realm' : current_realm,
                        'realms_count' : realms_count,
                    }


                    return render(request, 'accounts/attendance.html', context)
                except:
                    messages.add_message(request, messages.ERROR, "Something went wrong!")
                    return redirect(reverse('dashboard') + '?tab=new-attendance')
            else:
                return redirect('login')
        else:
            messages.add_message(request, messages.ERROR, "First, log in to your account!")
            return redirect('login')
        

    def post(self, request, pk):
        try:   
          if request.user.is_authenticated:
            attendance = Attendance.objects.get(id=pk)
            guild = Guild.objects.get(attendance=attendance)
            cut_dist = CutDistributaion.objects.get(attendance=attendance)
            
            attendance.cycle = Cycle.objects.get(id=request.POST['cycle'])
            attendance.run_type = RunType.objects.get(id=request.POST['run_type'])
            #attendance.status = request.POST['status']

            realm_type = request.POST['realm_method']
            attendance.date_time = request.POST['date_time']
            attendance.total_pot = request.POST['total_pot']
            attendance.boss_kill = request.POST['boss_kill']
            cut_dist.community = request.POST['community']
            guild.total = request.POST['total_guild']

            guild_refunds = request.POST['guild_refunds']
            guild_in_house_customer_pot = request.POST['guild_in_house_customer_pot']

            guild.gold_collector = request.POST['guild_gold_collector']
            guild.booster = request.POST['guild_booster']
            guild.guild_bank = request.POST['guild_bank']
            attendance.characters_name = request.POST['character_names']
            attendance.run_notes = request.POST['run_note']
            cut_dist.total_guild = guild
            cut_dist.save()
            attendance.save()
            guild.save()


            if ((not guild_in_house_customer_pot) or (not guild_in_house_customer_pot.isdigit())):
                guild_in_house_customer_pot = 0

            
            if ((not guild_refunds) or (not guild_refunds.isdigit())):
                guild_refunds = 0

            guild.in_house_customer_pot = guild_in_house_customer_pot
            guild.refunds = guild_refunds
            guild.save()

            indexes = list()

            player_ids = list()

            #get index of booster
            for key in request.POST.keys():
                if (key.split('_')[0] == 'booster'):
                    if key.split('_')[2] not in indexes:
                        indexes.append(key.split('_')[2])
            if indexes:


                #create boosters(Attendance Detail)
                booster_error = 0

                for index in indexes:
                    try:
                        username_id = request.POST['booster_username_' + index]
                        alt_id = request.POST['booster_alt_' + index]
                        alt = None
                        player = None

                            
                        try:
                            alt = Alt.objects.get(id=alt_id)
                        except:
                            alt = None

                        if username_id != "0":
                            player = User.objects.get(id=username_id)

                        role = Role.objects.get(id=request.POST['booster_role_' + index])
                        missing_boss = request.POST['missing_boss_' + index]
                        multiplier = request.POST['multiplier_' + index]
                        cut = request.POST['booster_cut_' + index]

                        if player:
                            try:
                                booster = AttendanceDetail.objects.get(attendane=attendance,player=player)
                                player_ids.append(booster.player.id)
                            except:
                                try:
                                    booster = AttendanceDetail.objects.create(attendane=attendance, player=player, alt=alt, role=role, missing_boss=missing_boss, cut=cut, multiplier=multiplier)
                                    booster.save()
                                    player_ids.append(booster.player.id)
                                    continue
                                except:
                                    booster_error += 1
                                    continue
                            else:
                                
                                if alt:
                                    if booster.alt == alt:
                                        booster.alt = alt
                                    else:
                                        booster = AttendanceDetail.objects.create(attendane=attendance, player=player, alt=alt, role=role, missing_boss=missing_boss, cut=cut, multiplier=multiplier)
                                        booster.save()
                                        player_ids.append(booster.player.id)
                                        continue
                                else:

                                    if booster.alt != alt:
                                        booster = AttendanceDetail.objects.create(attendane=attendance, player=player, alt=alt, role=role, missing_boss=missing_boss, cut=cut, multiplier=multiplier)
                                        booster.save()
                                        player_ids.append(booster.player.id)
                                        continue

                                booster.role = role
                                booster.missing_boss = missing_boss
                                booster.multiplier = multiplier
                                booster.cut = cut
                                booster.save()
                        else:
                            try:
                                ghost, alt, realm = alt_id.split('-')
                                realm = Realm.objects.get_or_create(name=realm)

                                alt = Alt.objects.get_or_create(name=alt, realm=realm[0], status="Verified")
                                AttendanceDetail.objects.create(attendane=attendance, role=role, player=None, alt=alt[0], missing_boss=missing_boss, multiplier=multiplier, cut=cut)
                            except:
                                booster_error += 1
                    except:
                        booster_error += 1





                deleted_booster = 0

                #Deleted booster    
                check_for_deleted = AttendanceDetail.objects.filter(attendane=attendance)
                exist_player = list()

                for index in indexes:
                    username_id = request.POST['booster_username_' + index]
                    alt_id = request.POST['booster_alt_' + index]
                    alt = None
                    player = None
                    
                    
                         
                    try:
                        alt = Alt.objects.get(id=alt_id)
                    except:
                        alt = None

                    if username_id != "0":
                        player = User.objects.get(id=username_id)
                    

                    if player:
                        try:
                            item = AttendanceDetail.objects.get(attendane=attendance, player=player, alt=alt)
                            exist_player.append(item)
                        except:
                            pass
                    else:
                        try:
                            ghost, alt, realm = alt_id.split('-')
                            realm = Realm.objects.get_or_create(name=realm)
                            alt = Alt.objects.get_or_create(name=alt, realm=realm[0])
                            item = AttendanceDetail.objects.get(attendane=attendance, player=None, alt=alt[0])
                            exist_player.append(item)

                        except:
                            pass


                for booster in check_for_deleted:
                    flag = False
                    for check_for_delete in exist_player:
                        if check_for_delete == booster:
                            flag = True
                            continue
                    
                    
                    if flag == False:
                        deleted_booster += 1
                        booster.delete()



                if booster_error > 0:
                    messages.add_message(request, messages.WARNING, f"{booster_error} booster, were not added")


                
                #if the realm type is multirealm
                if (realm_type == "2") or (realm_type == "1"):
                    realm_indexes = list()
                    realm_error = 0
                    for key in request.POST.keys():
                        if ((key.split('_')[0] == 'realm') and (key.split('_')[1] != 'method') and (key.split('_')[1] != 'amount')):
                            if (key.split('_')[1]) not in realm_indexes:
                                realm_indexes.append(key.split('_')[1])
                    
                    if realm_indexes:
                        for index in realm_indexes:
                            try:
                                realm_id = request.POST['realm_' + index]
                                amount = request.POST['realm_amount_' + index]  

                                if (int(amount) > 0) and (realm_id != "0"):
                                    realm = Realm.objects.get(id=realm_id)
                                    try:
                                        c_r = CurrentRealm.objects.get(attendance=attendance, realm=realm)
                                    except:
                                        CurrentRealm.objects.create(attendance=attendance, realm=realm, amount=amount)
                                    else:
                                        c_r.amount = amount
                                        c_r.save()
                                else:
                                    realm_error += 1
                            except:
                                realm_error += 1
                        
                        if realm_error > 0:
                            messages.add_message(request, messages.WARNING, f"{realm_error} realms, were not added")


                messages.add_message(request, messages.SUCCESS, "Attendance was saved successfully")
                return redirect("view_attendance" , attendance.id)
            
            else:
                ads = AttendanceDetail.objects.filter(attendane=attendance)
                for ad in ads:
                    ad.delete()

                messages.add_message(request, messages.SUCCESS, "Attendance was saved successfully")
                return redirect("view_attendance" , attendance.id)
          else:
            messages.add_message(request, messages.ERROR, "For bidden!")
            return redirect("dashboard")
        except:
            messages.add_message(request, messages.ERROR, "Something went wrong!")
            return redirect("view_attendance" , attendance.id)


        


class CreateAttendance(View):
    def get(self, request):
        if request.user.is_authenticated:
            if request.user.is_staff:
                try:
                    cycles = Cycle.objects.filter(status="O")
                    run_types = RunType.objects.filter()
                    date_time_form = DateTimeBootstrap(initial={'date_time': timezone.datetime.now()})
                    realms = Realm.objects.filter()
                    boosters = User.objects.filter(user_type__in=['O','A', 'B'])
                    alts = Alt.objects.filter(status="Verified")
                    roles = Role.objects.filter()
                    teams = Team.objects.filter()
                    specific_time = SpecificTime.objects.filter()
                    team_detail = TeamDetail.objects.filter()

                    context = {
                        'cycles' : cycles,
                        'run_types' : run_types,
                        'date_time_picker' : date_time_form,
                        'realms' : realms,
                        'boosters' : boosters,
                        'alts' : alts,
                        'roles' : roles,
                        'teams' : teams,
                        'specific_time' : specific_time,
                        'team_detail' : team_detail,
                    }
                 
                    return render(request, 'accounts/attendance.html', context)
                except:
                    messages.add_message(request, messages.ERROR, "Something went wrong!")
                    return redirect(reverse('dashboard') + '?tab=new-attendance')
                
            messages.add_message(request, messages.ERROR, "Something went wrong!")
            return redirect(reverse('dashboard') + '?tab=new-attendance')
        
        messages.add_message(request, messages.ERROR, "First, log in to your account!")
        return redirect('login')
    



    def post(self, request):
        try:
            if request.user.is_authenticated:
                cycle = Cycle.objects.get(id=request.POST['cycle'])
                run_type = RunType.objects.get(id=request.POST['run_type'])
                #status = request.POST['status']
                realm_type = request.POST['realm_method']
                date_time = request.POST['date_time']
                total_pot = request.POST['total_pot']
                boss_kill = request.POST['boss_kill']
                community = request.POST['community']
                total_guild = request.POST['total_guild']
                guild_refunds = request.POST['guild_refunds']
                guild_in_house_customer_pot = request.POST['guild_in_house_customer_pot']
                guild_gold_collector = request.POST['guild_gold_collector']
                guild_booster = request.POST['guild_booster']
                guild_bank = request.POST['guild_bank']
                character_names = request.POST['character_names']
                run_note = request.POST['run_note']


                indexes = list()

                if cycle and run_type and date_time and total_pot and boss_kill:

                    #get index of booster
                    for key in request.POST.keys():
                        if (key.split('_')[0] == 'booster'):
                            if key.split('_')[2] not in indexes:
                                indexes.append(key.split('_')[2])

                    if indexes:
                        if ((not guild_in_house_customer_pot) or (not guild_in_house_customer_pot.isdigit())):
                            guild_in_house_customer_pot = 0

                        
                        if ((not guild_refunds) or (not guild_refunds.isdigit())):
                            guild_refunds = 0

                        #create attendance
                        attendance = Attendance.objects.create(cycle=cycle, run_type=run_type, status='A', date_time=date_time, total_pot=total_pot, boss_kill=boss_kill, run_notes=run_note, characters_name=character_names)
                        attendance.save()

                        #create guild
                        guild = Guild.objects.create(attendance=attendance, booster=guild_booster, gold_collector=guild_gold_collector, guild_bank=guild_bank, total=total_guild, in_house_customer_pot=guild_in_house_customer_pot, refunds=guild_refunds)
                        guild.save()
                        
                        #create cut distributaion
                        CutDistributaion.objects.create(attendance=attendance, total_guild=guild, community=community)



                        #create boosters(Attendance Detail)
                        booster_error = 0
                        for index in indexes:
                            try:
                                username_id = request.POST['booster_username_' + index]
                                alt_id = request.POST['booster_alt_' + index]
                                alt = None
                                player = None

                                try:
                                    alt = Alt.objects.get(id=alt_id)
                                except:
                                    alt = None

                                if username_id != "0":
                                    player = User.objects.get(id=username_id)

                                role = Role.objects.get(id=request.POST['booster_role_' + index])
                                missing_boss = request.POST['missing_boss_' + index]
                                multiplier = request.POST['multiplier_' + index]
                                cut = request.POST['booster_cut_' + index]
                                
                                if (alt != None):
                                    if player != None:
                                        AttendanceDetail.objects.create(attendane=attendance, role=role, player=player, alt=alt, missing_boss=missing_boss, multiplier=multiplier, cut=cut)
                                    else:
                                        AttendanceDetail.objects.create(attendane=attendance, role=role, player=None, alt=alt, missing_boss=missing_boss, multiplier=multiplier, cut=cut)
                                else:
                                    try:
                                        ghost, alt, realm = alt_id.split('-')
                                        realm = Realm.objects.get_or_create(name=realm)

                                        alt = Alt.objects.get_or_create(name=alt, realm=realm[0], status="Verified")
                                        AttendanceDetail.objects.create(attendane=attendance, role=role, player=None, alt=alt[0], missing_boss=missing_boss, multiplier=multiplier, cut=cut)
                                    except:
                                        booster_error += 1
                            except:
                                booster_error += 1

                        if booster_error > 0:
                            messages.add_message(request, messages.WARNING, f"{booster_error} booster, were not added")


                        
                        #if the realm type is multirealm
                        if (realm_type == "2") or (realm_type == "1"):
                            realm_indexes = list()
                            realm_error = 0
                            for key in request.POST.keys():
                                if ((key.split('_')[0] == 'realm') and (key.split('_')[1] != 'method') and (key.split('_')[1] != 'amount')):
                                    if (key.split('_')[1]) not in realm_indexes:
                                        realm_indexes.append(key.split('_')[1])

                            if realm_indexes:
                                for index in realm_indexes:
                                    try:
                                        realm_id = request.POST['realm_' + index]
                                        amount = request.POST['realm_amount_' + index]  
                                        if (int(amount) > 0) and (realm_id != "0"):
                                            realm = Realm.objects.get(id=realm_id)
                                            CurrentRealm.objects.create(attendance=attendance, realm=realm, amount=amount)
                                        else:
                                            realm_error += 1
                                    except:
                                        realm_error += 1
                                
                                if realm_error > 0:
                                    messages.add_message(request, messages.WARNING, f"{realm_error} realms, were not added")

                        messages.add_message(request, messages.SUCCESS, "Attendance was created successfully")
                        return redirect(reverse('dashboard') + '?tab=new-attendance')

                        

                            
                
                messages.add_message(request, messages.WARNING, 'All fields except run_note and character_names are mandatory')
                return redirect('create_attendance')
        except:
            messages.add_message(request, messages.ERROR, 'Something went wrong!')
            return redirect('dashboard')
        


class TimeAdd(View):
    def post(self, request):
        try:
            time = request.POST['time']
            time = datetime.datetime.strptime(time, '%H:%M')

            SpecificTime.objects.create(time=time)
            messages.add_message(request, messages.SUCCESS, 'Specific Time added successfully')
        except:
            messages.add_message(request, messages.ERROR, 'there is a problem to add Specific Time')
        return redirect('create_attendance')





class TimeRemove(View):
    def get(self, request, pk):
        try:
            SpecificTime.objects.get(id=pk).delete()
            messages.add_message(request, messages.SUCCESS, 'Specific Time deleted successfully')
        except:
            messages.add_message(request, messages.ERROR, 'there is a problem to delete Specific Time')

        return redirect('create_attendance')
    

class RegisterGhostBooster(View):
    def get(self, request):
        data = json.loads(request.GET.get('array'))
        for obj in data:
            alt = obj.split(" ")[0]
            realm = obj.split(" ")[1]
            
            try:
                User.objects.create(username="ghost", email="ghost@ghost.com", password="")
            except:
                pass
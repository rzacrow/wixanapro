from django.contrib import admin
from .models import Attendance, AttendanceDetail, Role, RunType, Guild, CutInIR, CutDistributaion, CurrentRealm, Cycle, Payment
from django.db import models
from django.conf import settings
from django.db.models import Sum
from accounts.models import Wallet, Transaction, Notifications, Realm, Alt as booster_alt
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django import forms
from unfold.admin import ModelAdmin,TabularInline, StackedInline
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.widgets import UnfoldAdminSplitDateTimeWidget

class GuildInline(StackedInline):
    model = Guild
    readonly_fields = ['total', 'booster', 'gold_collector', 'guild_bank']
    extra = 1
    fieldsets = [(
            "",
            {
                'fields' : [('in_house_customer_pot', 'refunds'), ('total', 'booster'), ('gold_collector', 'guild_bank')]
            }
        )
    ]

    def save_model(self, request, obj, form, change):
        obj.total += obj.in_house_customer_pot
        obj.total -= obj.refunds
        obj.save()
        super().save_model(request, obj, form, change)



@admin.register(Transaction)
class TransactionAdmin(ModelAdmin):
    @admin.display(description="Date Time")
    def created_show(self, obj):
        return obj.created.strftime("%Y-%m-%d %H:%M")
    
    @admin.display(description="User")
    def user_requester(self, obj):
        if obj.alt:
            return obj.alt
        return obj.requester
    
    @admin.display(description="Amount")
    def amount_if_cut(self, obj):
        if obj.currency == 'CUT':
            if obj.amount >= 1000:
                return f"{obj.amount // 1000} K"
        return obj.amount
    
    list_display = ['user_requester', 'status', 'created_show', 'currency', 'amount_if_cut']
    readonly_fields = ['created_show']
    fieldsets = [(
            None,
            {
                'fields' : [('requester', 'created_show'), ('currency', 'amount'), ('status', 'caption'), ('card_detail', 'alt'), 'paid_date']
            }
        )
    ]

    ordering = ['status', '-created']
    search_fields = ["id"]
    search_help_text = ["Search in id"]


    list_filter_submit = True
    list_filter = ['status', 'created']


    def change_paid(self, request, objects):
        for obj in objects:
            Notifications.objects.create(send_to=obj.requester, title="Payment status changed", caption=f"Your payment request was changed to {obj.status} with code {obj.id}. This may take some time")
            obj.paid_date = timezone.now().today()
            obj.save()

    @admin.action(description="Change selected transactions status to 'Paid'")
    def change_to_paid(self, request, queryset):
        list_ids = queryset.values_list('id', flat=True)
        objects = Transaction.objects.filter(id__in=list_ids)
        self.change_paid(request=request, objects=objects)
        queryset.update(status='PAID')

    actions = ['change_to_paid']



    def save_model(self, request, obj, form, change):
        if 'status' in form.changed_data:
            if obj.status == 'PAID':
                self.change_paid(request=request, objects=[obj])
        super().save_model(request, obj, form, change)


class CutDistributaionInline(StackedInline):
    model = CutDistributaion
    list_display = ['total_guild', 'community']
    readonly_fields = ['total_guild', 'community']

class AttendanceDetailInline(TabularInline):
    model = AttendanceDetail
    extra = 2

    fieldsets = (
        (None, {
            "fields": [
                ('role', 'player'), 'alt', 'missing_boss', 'cut'   
            ],
        }),
    )

class CurrentRealmInline(TabularInline):
    model = CurrentRealm
    extra = 1



@admin.register(Role)
class RoleAdmin(ModelAdmin):
    list_display = ['id','name', 'ratio']

@admin.register(RunType)
class RunTypeAdmin(ModelAdmin):
    list_display = ['name', 'guild', 'community']
    fieldsets = (
        (None, {
            "fields": (
                'name',
                'guild',
                'community',
            ),
        }),
    )

    def save_model(self, request, obj, form, change):
        sum_of_value = (float(obj.guild) + float(obj.community))

        if sum_of_value != 100:
            messages.add_message(request, messages.WARNING, "The sum of the entered percentages is not equal to 100")
        super().save_model(request, obj, form, change)
    


@admin.register(CutInIR)
class CutInIR(ModelAdmin):
    @admin.display(description="Defined in")
    def date_time_show(self, obj):
        return obj.date_time.strftime("%Y-%m-%d")
    list_display = ['amount', 'date_time_show']

class at_in_form(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['date_time', 'status', 'total_pot']

        labels = {
            'status' : "Status",
            'total_pot' : 'Total pot'

        }


class AttendanceInline(StackedInline):
    model = Attendance
    form = at_in_form

    fieldsets = (
            (None, {
                "fields": (
                    'date_time',
                    ('status' , 'total_pot')
                ),
            }),
        )
    extra = 1


@admin.register(Cycle)
class CycleAdmin(ModelAdmin):
    @admin.display(description="Start Date")
    def start_date_display(self, obj):
        try:
            return obj.start_date.strftime('%Y-%m-%d')
        except:
            return None
    
    @admin.display(description="End Date")
    def end_date_display(self, obj):
        try:
            return obj.end_date.strftime('%Y-%m-%d')
        except:
            return None
        
    list_display = ['start_date_display', 'end_date_display', 'status']
    ordering = ['-start_date']

    list_filter = [
        'start_date',
        'end_date',
        'status',
    ]

    inlines = [
        AttendanceInline
    ]

    list_filter_submit = True  # Submit button at the bottom of the filter

    def closed_status(self, request, objects):
        for obj in objects:
                if obj.status == 'C':
                    continue
                attendances = Attendance.objects.filter(cycle=obj)
                if attendances:
                    for at in attendances:
                        boosters = AttendanceDetail.objects.filter(attendane=at)
                        if at.status == 'A':
                            at.status = 'C'
                            if at.paid_status == False:
                                if boosters:
                                    for b in boosters:
                                        wallet = Wallet.objects.get_or_create(player=b.player)
                                        wallet[0].amount += b.cut
                                        wallet[0].save()
                                    at.paid_status = True                                    
                            at.save()
                        if boosters:
                            for booster in boosters:
                                string = f"1"
                                Payment.objects.create(cycle=obj, detail=booster, string=string)

    @admin.action(description="Change to 'Close'")
    def change_status_to_close(self, request, queryset):
        list_ids = queryset.values_list('id', flat=True)
        objects = Cycle.objects.filter(id__in=list_ids)
        self.closed_status(request=request, objects=objects)
        queryset.update(status='C')

    actions = [
        'change_status_to_close'
    ]

    def save_model(self, request, obj, form, change):
        if 'status' in form.changed_data:
            if obj.status == 'C':
                self.closed_status(request=request, objects=[obj])
        super().save_model(request, obj, form, change)



@admin.register(Payment)
class PaymentAdmin(ModelAdmin):

    @admin.display(description="User")
    def user_display(self, obj):
        return obj.detail.player
    
    @admin.display(description="Payment character")
    def payment_character(self, obj):
        try:
            return obj.payment_character
        except:
            return "there aren't any payment character"
    
    @admin.display(description="Cut")
    def booster_cut(self, obj):
        if obj.detail.cut >= 1000:
            amount_per_thousand = obj.detail.cut // 1000
            return f"{amount_per_thousand} K"
        return obj.detail.cut
    
    list_display = ['user_display', 'payment_character', 'booster_cut', 'string','is_paid']
    ordering = ['cycle__end_date']

    def is_paid_change(self, objects, request):
        for obj in objects:
            try:
                wallet = Wallet.objects.get(player=obj.detail.player)
            except:
                messages.add_message(request, messages.ERROR, message=f"There was a problem in deducting the payment amount from user {obj.detail.player} wallet")
                obj.is_paid = False
                obj.save()
            else:
                wallet.amount -= int(obj.detail.cut)
                wallet.save()
                Transaction.objects.create(requester=obj.detail.player, status='PAID', paid_date=timezone.now().today(), amount=obj.detail.cut, currency='CUT', alt=obj.detail.payment_character)


    @admin.action(description="Paid status to 'True'")
    def change_to_ispaid(self, request, queryset):
        list_ids = queryset.values_list('id', flat=True)
        objects = Payment.objects.filter(id__in=list_ids)
        self.is_paid_change(objects=objects, request=request)
        queryset.update(is_paid=True)

    actions = [
        'change_to_ispaid'
    ]

    def save_model(self, request, obj, form, change):
        if 'is_paid' in form.changed_data:
            if obj.is_paid == True:
                self.is_paid_change(objects=[obj], request=request)

        super().save_model(request, obj, form, change)
                


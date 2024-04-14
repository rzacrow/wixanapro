from django.contrib import admin
from django.contrib.auth.models import User, Group, Permission
from .models import User as um, Team, TeamDetail, Alt, Realm, Wallet, Notifications, Loan, Debt, WixanaBankDetail, PaymentDebtTrackingCode, Ticket, TicketAnswer, CardDetail, InviteMember
from django.db import models
from unfold.admin import ModelAdmin,TabularInline, StackedInline
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.forms import UserCreationForm
from django.contrib.auth.admin import GroupAdmin as gAdmin,UserAdmin as BaseUserAdmin
from django.conf import settings
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django import forms


admin.site.unregister(Group)

@admin.register(Group)
class GroupAdmin(gAdmin,ModelAdmin):
    list_display = ['name']

@admin.register(InviteMember)
class InviteMemberAdmin(ModelAdmin):
    list_display = ['user', 'answer']
    
@admin.register(Realm)
class Realm(ModelAdmin):
    # Preprocess content of readonly fields before render
    readonly_preprocess_fields = {
        "model_field_name": "html.unescape",
        "other_field_name": lambda content: content.strip(),
    }

    formfield_overrides = {
        models.TextField: {
            "widget": WysiwygWidget,
        }
    }

class WalletInline(StackedInline):
    model = Wallet
    # Preprocess content of readonly fields before render
    readonly_preprocess_fields = {
        "model_field_name": "html.unescape",
        "other_field_name": lambda content: content.strip(),
    }


class AltInline(TabularInline):
    model = Alt
    # Preprocess content of readonly fields before render
    readonly_preprocess_fields = {
        "model_field_name": "html.unescape",
        "other_field_name": lambda content: content.strip(),
    }
    extra = 1

@admin.register(Alt)
class AltAdmin(ModelAdmin):
    list_display = ['name','player', 'status']
    ordered = ['status']

    actions = [
        'change_alts_verified',
        'change_alts_rejected'
    ]

    @admin.action(description="Change selected alts to 'Verified'")
    def change_alts_verified(self, request, queryset):
        queryset.update(status='Verified')

    @admin.action(description="Change selected alts to 'Rejected'")
    def change_alts_rejected(self, request, queryset):
        queryset.update(status='Rejected')


    def save_model(self, request, obj, form, change):
        if 'status' in form.changed_data:
            Notifications.objects.create(send_to=obj.player, title="Alt status", caption=f"Your Alt {obj.name} status changed by admin")
        super().save_model(request, obj, form, change)




def get_user_permission(user):
    if user.is_superuser:
        return Permission.objects.all()
    return user.user_permissions.all() | Permission.objects.filter(group__user=user)

def add_user_permission():
    admin_perm = Permission.objects.exclude(content_type__app_label='accounts', codename='add_user')
    admin_perm = admin_perm.exclude(content_type__app_label='accounts', codename='change_user')
    admin_perm = admin_perm.exclude(content_type__app_label='accounts', codename='delete_user')

    admin_perm = admin_perm.exclude(content_type=ContentType.objects.get(model='session'))
    return admin_perm


@admin.register(um)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    add_form = UserCreationForm

    def changeform_view(self, request, obj, form, change):
        if request.user.user_type != 'O':
            raise PermissionDenied()
        
        try:
            user = um.objects.get(id=obj)
            if user:
                if user.user_type != 'U':
                    self.inlines = [
                        AltInline,
                        WalletInline
                    ]
                else:
                    self.inlines = [
                    ]
        except:
            pass

        ONE_MONTH = 30 * 24 * 60 * 60
        expiry = getattr(settings, "KEEP_LOGGED_DURATION", ONE_MONTH)
        request.session.set_expiry(expiry)
        return super().changeform_view(request, obj, form, change)


    @admin.display(description="Lost Login")
    def lost_login_show(self, obj):
        try:
            return obj.last_login.strftime("%Y-%m-%d")
        except:
            return None
    
    list_display = ['nick_name', 'username', 'user_type', 'lost_login_show']
    list_display_links = ['nick_name', 'username']
    fieldsets = [
        (
            "User info",
            {
                'fields' : [('username', 'user_type'), ('nick_name', 'phone'), 'national_code', 'avatar', ('email', 'discord_id'), 'groups', 'is_staff', ('last_login', 'date_joined'), ]
            }
        )
    ]

    search_fields = ["username"]
    search_help_text = ["Search in username"]
    
    readonly_fields = ['last_login', 'date_joined']
    # Preprocess content of readonly fields before render
    readonly_preprocess_fields = {
        "model_field_name": "html.unescape",
        "other_field_name": lambda content: content.strip(),
    }


    # Display submit button in filters
    list_filter_submit = True
    list_filter = ['user_type']
    actions = ['change_user_to_booster']
    actions_selection_counter = True
    
    # Custom actions
    actions_list = []  # Displayed above the results list
    actions_row = []  # Displayed in a table row in results list
    actions_detail = []  # Displayed at the top of for in object detail
    actions_submit_line = []  # Displayed near save in object detail

    formfield_overrides = {
        models.TextField: {
            "widget": WysiwygWidget,
        }
    }

    @admin.action(description="Change access to booster level")
    def change_user_to_booster(self, request, queryset):
        queryset.update(user_type="B")


    def get_ordering(self, request):
        return ["username"]
    
    def save_model(self, request, obj, form, change):        
        if obj.user_type == 'B':
            try:
                get_wallet = Wallet.objects.get(player__username=obj.username)
            except:
                Wallet.objects.create(player=obj)

        if 'user_type' in form.changed_data:
            if request.user.user_type == 'O':
                if obj.user_type == 'A':
                    obj.is_staff = True
                    obj.save()
                elif (obj.user_type == 'B') or (obj.user_type == 'U'):
                    obj.is_staff = False
                    obj.is_superuser = False
                    obj.save()
                elif obj.user_type == 'O':
                    obj.is_staff = True
                    obj.is_superuser = True
                    obj.save()
            else:
                raise PermissionDenied()
            Notifications.objects.create(send_to=obj, title="Change User Permission", caption=f"your profile permission changed to the '{obj.user_type}' level by Owner")
        
        super().save_model(request, obj, form, change)


class TeamDetailInline(TabularInline):
    model = TeamDetail
    extra = 1
    
@admin.register(Team)
class TeamAdmin(ModelAdmin):
    list_display = ['name', 'status']

    inlines = [
        TeamDetailInline
    ]
    @admin.action(description="Change status to 'Verified'")
    def change_status_verified(self, request, queryset):
        queryset.update(status="Verified")

    actions = [
        'change_status_verified'
    ]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.status == 'Rejected':
            leader = TeamDetail.objects.filter(team=obj).first()
            Team.objects.get(id=obj.id).delete()
            Notifications.objects.create(send_to=leader.player, title="Your team has been deleted by the admin")


@admin.register(Loan)
class LoanAdmin(ModelAdmin):
        
        @admin.display(description="Amount")
        def amount_disp(self, obj):
            if obj.method == 'CUT':
                return f'{obj.amount} K'
            else:
                return f'{obj.amount} T'

    
        list_display = ['user', 'method', 'loan_status','amount_disp']
        ordering = ['-created_at']

        list_filter = ['loan_status', 'created_at']


        def change_status_accept_do(self, request, objects):
            for obj in objects:
                Debt.objects.create(loan=obj, debt_amount=obj.amount, paid_status='UnPaid')


        @admin.action(description="Change status to 'Accept'")
        def change_status_accept(self, request, queryset):
            queryset.update(loan_status="Accept")
            list_ids = queryset.values_list('id', flat=True)
            objects = Loan.objects.filter(id__in=list_ids)
            self.change_status_accept_do(request=request, objects=objects)


        @admin.action(description="Change status to 'Reject'")
        def change_status_reject(self, request, queryset):
            queryset.update(loan_status="Reject")

        actions = [
            'change_status_reject',
            'change_status_accept'
        ]

        def save_model(self, request, obj, form, change):
            super().save_model(request, obj, form, change)
            if 'loan_status' in form.changed_data:
                if obj.loan_status == 'Reject':
                    Notifications.objects.create(send_to=obj.user, title="Loan request", caption="Your loan request was rejected by the admin")
                    obj.loan_status = 'Reject'
                    obj.save()

                if obj.loan_status == 'Accept':
                    Notifications.objects.create(send_to=obj.user, title="Loan request", caption="Your loan request was Accepted by the admin")
                    obj.loan_status = 'Accept'
                    obj.save()
                    Debt.objects.create(loan=obj, debt_amount=obj.amount, paid_status='UnPaid')
   


@admin.register(WixanaBankDetail)
class WixanaBankDetailAdmin(ModelAdmin):
    list_display = ['card_name', 'card_number']


@admin.register(PaymentDebtTrackingCode)
class PaymentDebtTrackingCodeAdmin(ModelAdmin):


    def changeform_view(self, request, obj, form, change):
        if request.user.user_type != 'O':
            raise PermissionDenied()
        return super().changeform_view(request, obj, form, change)

    @admin.display(description="User")
    def username(self, obj):
        name = obj.debt.loan.user.username
        if obj.debt.loan.user.nick_name:
            name = obj.debt.loan.user.nick_name
        return name
    
    @admin.display(description='Status')
    def status(self, obj):
        return obj.payment_debt_status
    
    @admin.display(description='Amount')
    def amount_in_ir(self, obj):
        if obj.debt.loan.method == 'CUT':
            return f"{obj.debt_amount_IR} K"
        else:
            return f"{obj.debt_amount_IR} T"

    @admin.display(description='Method')
    def debt_method(self, obj):
        name = obj.debt.loan.method
        return name
    


    list_display = ['username','tracking_code', 'status', 'amount_in_ir', 'debt_method']
    ordering = ['-created']


    def change_status_accept_do(self, request, objects):
        for obj in objects:
            Notifications.objects.create(send_to=obj.debt.loan.user, title="Payment receipts", caption="Your payment receipt was Accepted by the admin, Your debt has been settled")
            debt = Debt.objects.get(id=obj.debt.id)
            debt.paid_status = 'Paid'
            debt.debt_amount = 0
            debt.save()


    def change_status_reject_do(self, request, objects):
        for obj in objects:
            Notifications.objects.create(send_to=obj.debt.loan.user, title="Payment receipts", caption="Your payment receipt was rejected by the admin")


    @admin.action(description="Change status to 'Accepted'")
    def change_status_accept(self, request, queryset):
        queryset.update(payment_debt_status="Accepted")
        list_ids = queryset.values_list('id', flat=True)
        objects = PaymentDebtTrackingCode.objects.filter(id__in=list_ids)
        self.change_status_accept_do(request, objects)


    @admin.action(description="Change status to 'Rejected'")
    def change_status_reject(self, request, queryset):
        queryset.update(payment_debt_status="Rejected")
        list_ids = queryset.values_list('id', flat=True)
        objects = PaymentDebtTrackingCode.objects.filter(id__in=list_ids)
        self.change_status_reject_do(request, objects)

    actions = [
        'change_status_reject',
        'change_status_accept'
    ]


    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if 'payment_debt_status' in form.changed_data:
            if obj.payment_debt_status == 'Accepted':
                Notifications.objects.create(send_to=obj.debt.loan.user, title="Payment receipts", caption="Your payment receipt was Accepted by the admin, Your debt has been settled")
                debt = Debt.objects.get(id=obj.debt.id)
                debt.paid_status = 'Paid'
                debt.debt_amount = 0
                debt.save()

            elif obj.payment_debt_status == 'Rejected':
                Notifications.objects.create(send_to=obj.debt.loan.user, title="Payment receipts", caption="Your payment receipt was rejected by the admin")



@admin.register(Debt)
class DebtAdmin(ModelAdmin):
    def changeform_view(self, request, obj, form, change):
        if request.user.user_type != 'O':
            raise PermissionDenied()
        return super().changeform_view(request, obj, form, change)
    


    @admin.display(description="User")
    def username(self, obj):
        name = obj.loan.user.username
        if obj.loan.user.nick_name:
            name = obj.loan.user.nick_name
        return name
    

    
    @admin.display(description="Method")
    def debt_method(self, obj):
        name = obj.loan.method
        return name
    

    @admin.display(description='Debt amount')
    def amount_in_ir(self, obj):
        if obj.loan.method == 'CUT':
            return f"{obj.debt_amount} K"
        else:
            return f"{obj.debt_amount} T"

    
    list_display = ['username', 'amount_in_ir', 'paid_status', 'debt_method']

class CardDetailInline(TabularInline):
    model = CardDetail

@admin.register(Wallet)
class WalletAdmin(ModelAdmin):
    def changeform_view(self, request, obj, form, change):
        if request.user.user_type != 'O':
            raise PermissionDenied()
        return super().changeform_view(request, obj, form, change)
    
    @admin.display(description="Balance")
    def balance_show(self, obj):
        if obj.amount >= 1000:
            return "{0} K".format(obj.amount // 1000)
        return obj.amount
    
    list_display = ['player', 'balance_show']
    readonly_fields = ['player']

    inlines = [
        CardDetailInline
    ]


class TicketAnswerInline(StackedInline):
    model = TicketAnswer
    extra = 1


@admin.register(Ticket)
class TicketAdmin(ModelAdmin):
    @admin.display(description="Postage date")
    def created_date(self, obj):
        return obj.created.strftime("%Y-%m-%d %H:%M")
    

    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super(TicketAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'text':
            formfield.widget = forms.Textarea(attrs=formfield.widget.attrs)
        return formfield
    
    inlines = [
        TicketAnswerInline
    ]
    
    list_display = ['user', 'title', 'created_date', 'status']
    ordering = ['-created']

    @admin.action(description="Change status to 'Answered'")
    def change_status_answered(self, request, queryset):
        queryset.update(status="ANSWERED")

    actions = [
        'change_status_answered',
    ]
    def save_model(self, request, obj, form, change):
        try:
            ticket = TicketAnswer.objects.filter(ticket=obj)
            if ticket:
                if ticket != '':
                    obj.status = 'ANSWERED'
                    obj.save()
        except:
            pass
        super().save_model(request, obj, form, change)


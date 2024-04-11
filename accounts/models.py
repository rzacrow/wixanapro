from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
class User(AbstractUser):
    def generate_unique_path(self, filename):
        return f"profile/{self.username}/{filename}"
    
    USER_TYPE_CHOICES = (
        ('O', 'Owner'),
        ('A', 'Admin'),
        ('B','Booster'),
        ('U', 'User')
    )

    AUTHENTICATION_LEVEL = (
        ('White', 'White'),
        ('Yellow', 'Yellow'),
        ('Green', 'Green'),
    )

    avatar = models.ImageField(upload_to=generate_unique_path, blank=True, null=True)
    email = models.CharField(unique=True, max_length=256, blank=False, null=False)
    user_type = models.CharField(max_length=1, choices=USER_TYPE_CHOICES, blank=False, null=False, default="U")
    discord_id = models.CharField(max_length=256, blank=True, null=True)
    avatar_hash = models.CharField(max_length=256, blank=True, null=True)
    national_code = models.CharField(max_length=10, blank=True, null=True, unique=True)
    phone = models.CharField(max_length=11, unique=True, blank=True, null=True)
    nick_name = models.CharField(max_length=128, blank=True, null=True)
    authentication_level = models.CharField(max_length=6, choices=AUTHENTICATION_LEVEL, default='White')
    
    def __str__(self) -> str:
        if self.nick_name:
            return self.nick_name
        else:
            return self.username
    

class Wallet(models.Model):
    player = models.OneToOneField(User, on_delete=models.CASCADE)
    amount = models.IntegerField(default=0, verbose_name="Balance")

    def __str__(self) -> str:
            if self.player.nick_name:
                return self.player.nick_name
            return self.player.username
    

class CardDetail(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    card_number = models.CharField(max_length=16, blank=False, null=False)
    shaba = models.CharField(max_length=24, blank=False, null=False)
    full_name = models.CharField(max_length=128, blank=False, null=False)

    def split_show_card(self):
        try:
            card_number = ""
            for i in range(len(self.card_number)):
                if ((i) % 4) == 0:
                    card_number += '\t\t'
                card_number += self.card_number[i]
            return card_number

        except:
            return None
        
    def split_show_shaba(self):
        try:
            card_number = ""
            for i in range(len(self.shaba)):
                if i == 2:
                    card_number += '\t\t'
                if ((i+2) % 4) == 0:
                    card_number += '\t\t'
                card_number += self.shaba[i]
            return card_number

        except:
            return None
        
    def __str__(self) -> str:
        try:
            return self.split_show_card()
        except:
            return None

class Realm(models.Model):
    name = models.CharField(max_length=128, blank=False, null=False)
    def __str__(self) -> str:
        return self.name
    

class Alt(models.Model):
    ALT_STATUS_CHOICES = (
        ('Verified', 'Verified'),
        ('Awaiting', 'Awaiting'),
        ('Rejected', 'Rejected')
    )

    player = models.ForeignKey(User, on_delete=models.CASCADE, blank=False, null=False)
    name = models.CharField(max_length=128, blank=False, null=False)
    status = models.CharField(max_length=8, choices=ALT_STATUS_CHOICES, default='Awaiting')
    realm = models.ForeignKey(Realm, on_delete=models.PROTECT)
    def __str__(self) -> str:
        return f"{self.name}-{self.realm.name}"


class RemoveAltRequest(models.Model):
    REMOVE_ALT_REQUEST_STATUS = (
        ('Accept','Accept'),
        ('Awaiting','Awaiting'),
        ('Reject','Reject'),
    )

    alt = models.ForeignKey(Alt, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=8, choices=REMOVE_ALT_REQUEST_STATUS)


class Team(models.Model):
    TEAM_STATUS_CHOICES = (
        ('Verified','Verified'),
        ('Pending','Pending'),
        ('Rejected','Rejected'),
    )
    name = models.CharField(max_length=128, blank=False, null=False)
    team_url = models.CharField(max_length=258, blank=True, null=True)
    status = models.CharField(max_length=8, default='Pending', choices=TEAM_STATUS_CHOICES)

    def __str__(self) -> str:
        return self.name


@receiver(post_save, sender=Team)
def populate_parents(sender, instance, created, **kwargs):
    if created:
        instance.team_url = f"{settings.ALLOWED_HOSTS[0]}/dashboard/team/{instance.id}/"
        instance.save()


class TeamDetail(models.Model):
    ROLE_TEAM_CHOICES = (
        ('Leader', 'Leader'),
        ("Admin", "Admin"),
        ('Member', 'Member'),
    )
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    team_role = models.CharField(max_length=6, choices=ROLE_TEAM_CHOICES, default="Member")
    def __str__(self) -> str:
        return f"{self.team.name} | {self.player.username}"
    
class TeamRequest(models.Model):
    TEAM_STATUS_CHOICES = (
        ('Verified', 'Verified'),
        ('Awaiting', 'Awaiting'),
        ('Rejected', 'Rejected')
    )

    player = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    status = models.CharField(max_length=8, choices=TEAM_STATUS_CHOICES, default='Awaiting')

class InviteMember(models.Model):
    INVITE_ANSWER = (
        ("Accept", "Accept"),
        ("Reject", "Reject"),
        ("Pending", "Pending"),
    )
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    answer = models.CharField(max_length=7, choices=INVITE_ANSWER)

class Notifications(models.Model):
    NOTIF_CHOICES = (
        ('S', 'Seen'),
        ('U', 'Unseen'),
    )

    send_to = models.ForeignKey(User, on_delete = models.CASCADE)
    title = models.CharField(max_length=48)
    caption = models.CharField(max_length=255, blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=1, choices=NOTIF_CHOICES, default='U')


class Transaction(models.Model):
    TRANSACTION_CHOICES = (
        ('PAID', 'Paid'),
        ('ACTIVE', 'Active'),
    )

    CURRENCY_CHOICES = (
        ('CUT', 'Cut'),
        ('IR', 'IR'),
    )

    requester = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=6, choices=TRANSACTION_CHOICES, default='ACTIVE')
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    caption = models.CharField(max_length=255, blank=True, null=True)
    paid_date = models.DateTimeField(blank=True, null=True)
    amount = models.IntegerField(default=0)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='CUT')
    alt = models.ForeignKey(Alt, on_delete=models.CASCADE, blank=True, null=True)
    card_detail = models.ForeignKey(CardDetail, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self) -> str:
        return str(self.id)
    

class Loan(models.Model):
    LOAN_STAUTS = (
        ('Pending','Pending'),
        ('Accept','Accept'),
        ('Reject','Reject'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    alt = models.ForeignKey(Alt, on_delete=models.CASCADE, blank=True, null=True)
    note = models.CharField(max_length=255, blank=True, null=True)
    loan_status = models.CharField(max_length=7, default='Pending', choices=LOAN_STAUTS)

    def __str__(self) -> str:
        name = self.user.username
        if self.user.nick_name:
            name = self.user.nick_name
        return f"{name}|{self.loan_status}"


class Debt(models.Model):
    DEBT_PAID_STATUS = (
        ('UnPaid','UnPaid'),
        ('Paid','Paid')
    )

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE)
    debt_amount = models.IntegerField()
    paid_status = models.CharField(max_length=6, choices=DEBT_PAID_STATUS, default='UnPaid')

    def __str__(self) -> str:
        name = self.loan.user.username
        if self.loan.user.nick_name:
            name = self.loan.user.nick_name
        return f"{name} | cut: {str(self.debt_amount)} K"


class PaymentDebtTrackingCode(models.Model):
    PAYMENT_DEBT_VIA_TRACKING_CODE_STATUS = (
        ('Pending', 'Pending'),
        ('Rejected', 'Rejected'),
        ('Accepted', 'Accepted')
    )

    debt = models.ForeignKey(Debt, on_delete=models.CASCADE)
    tracking_code = models.CharField(max_length=50, null=False, blank=False, unique=True)
    payment_debt_status = models.CharField(choices=PAYMENT_DEBT_VIA_TRACKING_CODE_STATUS, max_length=8, default='Pending')
    debt_amount_IR = models.IntegerField()
    created = models.DateTimeField(default=timezone.datetime.now())

    def __str__(self) -> str:
        return self.tracking_code

class WixanaBankDetail(models.Model):
    card_number = models.CharField(max_length=16)
    card_name = models.CharField(max_length=30)

class Ticket(models.Model):
    TICKET_STATUS =(
        ('ANSWERED', 'Answered'),
        ('UNANSWERED', 'Unanswered'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=TICKET_STATUS, default='UNANSWERED')
    title = models.CharField(max_length=64, blank=False, null=False)
    text = models.CharField(max_length=555, blank=False, null=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title

class TicketAnswer(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    description = models.CharField(max_length=555, blank=False, null=False)
    created = models.DateTimeField(auto_now_add=True)

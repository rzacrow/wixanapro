from django.db import models
from accounts.models import User, Realm, Alt
from django.utils import timezone
from datetime import timedelta

class RunType(models.Model):
    name = models.CharField(max_length=128, blank=True, null=False)
    community = models.FloatField(default=63.5)
    guild = models.FloatField(default=27.5)
    def __str__(self) -> str:
        return self.name
    

class Cycle(models.Model):
    CYCLE_CHOICES = (
        ('O', 'Open'),
        ('C', 'Close'),
    )
    status = models.CharField(max_length=1, choices=CYCLE_CHOICES)
    start_date = models.DateTimeField(default=timezone.datetime.now())
    end_date = models.DateTimeField()
    

    @classmethod
    def create_or_get_latest(cls):
        latest = cls.objects.filter()
        if latest:
            if latest.last().status != "C":
                return latest.last().id
        cycle = cls.objects.get_or_create(
            status = 'O',
            defaults=dict(start_date = timezone.datetime.now() ,end_date=timezone.datetime.now() + timedelta(days=7))
        )
        return cycle[0].id

    def __str__(self) -> str:
        return (self.start_date.strftime('%Y-%m-%d %H:%M'))


class Attendance(models.Model):
    ATTENDANCE_CHOICES = (
        ('A', 'Active'),
        ('C', 'Closed')
    )
    INPUT_MEMEBERS_TYPE_CHOICES = (
        ('W', 'Website users'),
        ('C', 'Character name'),
    )

    date_time = models.DateTimeField(blank=False, null=False)
    run_type = models.ForeignKey(RunType, on_delete=models.PROTECT, blank=False, null=False)
    total_pot = models.IntegerField(blank=False, null=False)
    boss_kill = models.IntegerField(blank=False, null=False)
    run_notes = models.CharField(max_length=555, blank=True, null=True)
    status = models.CharField(max_length=1, choices=ATTENDANCE_CHOICES)
    characters_name = models.CharField(max_length=1024, blank=True, null=True)
    paid_status = models.BooleanField(default=False)
    cycle = models.ForeignKey(Cycle, on_delete=models.CASCADE, default=Cycle.create_or_get_latest)

    def __str__(self) -> str:
        return str(self.date_time)


class CurrentRealm(models.Model):
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE)
    realm = models.ForeignKey(Realm, on_delete=models.CASCADE, blank=True, null=True)
    amount = models.IntegerField(blank=True, null=True)

    def __str__(self) -> str:
        return f"{str(self.attendance.id)} - {self.realm.name} -> {self.amount}"

class Guild(models.Model):
    attendance = models.OneToOneField(Attendance, on_delete=models.CASCADE, default=None)
    booster = models.IntegerField(default=0)
    gold_collector = models.IntegerField(default=0)
    guild_bank = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    in_house_customer_pot = models.IntegerField(default=0) #sum by total
    refunds = models.IntegerField(default=0) #negative by total

    def __str__(self) -> str:
        return str(self.total)

class CutDistributaion(models.Model):
    attendance = models.OneToOneField(Attendance, on_delete=models.CASCADE)
    total_guild = models.OneToOneField(Guild, on_delete=models.CASCADE)
    community = models.IntegerField(default=0)


class Role(models.Model):
    name = models.CharField(max_length=128, blank=False, null=False)
    ratio = models.FloatField(default=1.00)

    def __str__(self) -> str:
        return self.name
    
    @classmethod
    def get_default_role(cls):
        role = cls.objects.filter()
        if role:
            return role.first().id
        role = cls.objects.get_or_create(
            name="booster",
            defaults=dict(ratio=1.0)
        )
        return role[0].id
    
    @classmethod
    def get_default_raidleader(cls):
        role = cls.objects.get_or_create(
            name="Raid leader",
            defaults=dict(ratio=1.5)
        )
        return role[0]
    
    @classmethod
    def get_default_assistant(cls):
        role = cls.objects.get_or_create(
            name="Assistant",
            defaults=dict(ratio=1.1)
        )
        return role[0]
    

class AttendanceDetail(models.Model):
    attendane = models.ForeignKey(Attendance, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, default=Role.get_default_role, null=True)
    player = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    alt = models.ForeignKey(Alt, on_delete=models.CASCADE, blank=True, null=True)
    missing_boss = models.IntegerField(default=0)
    multiplier = models.FloatField(default=1.0)
    cut = models.IntegerField(default=0)
    payment_character = models.ForeignKey(Alt, on_delete=models.CASCADE, blank=True, null=True, default=None, related_name="payment_character")

    def __str__(self) -> str:
        try:
            return self.alt.name
        except:
            try:
                name = self.player.username
                if self.player.nick_name:
                    name = self.player.nick_name
                return name
            except:
                return None


class Payment(models.Model):
    is_paid = models.BooleanField(default=False)
    cycle = models.ForeignKey(Cycle, on_delete=models.CASCADE)
    string = models.CharField(max_length=256, blank=True, null=True)
    paid_date = models.DateTimeField(blank=True, null=True)
    detail = models.ForeignKey(AttendanceDetail, on_delete=models.CASCADE, blank=True, null=True)

class SpecificTime(models.Model):
    time = models.TimeField()

    def __str__(self) -> str:
        return str(self.time)

class CutInIR(models.Model):
    amount = models.IntegerField()
    date_time = models.DateField(auto_now=True)
    def __str__(self) -> str:
        return str(self.amount)
    


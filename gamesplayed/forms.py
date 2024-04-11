from django import forms
from .models import Attendance, AttendanceDetail
from bootstrap_datepicker_plus.widgets import DateTimePickerInput


class DateTimeBootstrap(forms.Form):
    def __init__(self, *args, **kwargs):
        super(DateTimeBootstrap, self).__init__(*args, **kwargs)
        self.fields['date_time'].widget.attrs['class'] = 'date_time_field'
    date_time = forms.DateField(widget=DateTimePickerInput(options={'format': 'YYYY-MM-DD HH:mm'}), label="Date Time", )




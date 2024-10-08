from django.urls import path
from .views import ViewAttendance, CreateAttendance, TimeAdd, TimeRemove, RegisterGhostBooster, CyclePayment, RemoveAttendance


urlpatterns = [
    path('attendance/<int:pk>/', ViewAttendance.as_view(), name="view_attendance"),
    path('attendance/create/', CreateAttendance.as_view(), name="create_attendance"),
    path('attendance/time/add/', TimeAdd.as_view(), name='add_time'),
    path('attendance/time/remove/<int:pk>/', TimeRemove.as_view(), name='remove_time'),
    path('register/ghost/', RegisterGhostBooster.as_view(), name="register_ghost_booster"),
    path('attendance/remove/', RemoveAttendance.as_view(), name="remove_attendance"),

    path('cycle/payments/save/', CyclePayment.as_view() , name="cycle_payment")
]

from User.models import Entity,Department, User
from Asset.models import AssetClass, Asset, PendingRequests

def add_department():
    Department.objects.create()
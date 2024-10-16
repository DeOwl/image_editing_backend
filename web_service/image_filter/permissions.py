from rest_framework import permissions
from .redis import session_storage
from .models import CustomUser

class IsAuth(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            session_id = request.COOKIES['session_id']
            if session_id is None:
                return False
            session_storage.get(session_id).decode('utf-8')
        except:
            return False
        return True
    
class IsAuthManager(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            session_id = request.COOKIES['session_id']
            if session_id is None:
                return False
            email = session_storage.get(session_id).decode('utf-8')
        except:
            return False
        user = CustomUser.objects.filter(email=email).first()
        return user.is_staff
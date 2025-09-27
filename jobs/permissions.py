from rest_framework import permissions

class IsCompanyMemberOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if not hasattr(request.user, 'employer_profile'):
            return False

        return request.user.employer_profile.company == obj.company
    
class IsAdminOfApplicationCompany(permissions.BasePermission):
    def has_permission(self, request, view):

        return (request.user.is_authenticated and 
                hasattr(request.user, 'employer_profile') and
                request.user.employer_profile.is_company_admin)
    
    def has_object_permission(self, request, view, obj):

        if not hasattr(request.user, 'employer_profile'):
            return False
        
        user_company = request.user.employer_profile.company

        return user_company == obj.job.company
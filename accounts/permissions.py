from rest_framework import permissions

class IsCompanyAdmin(permissions.BasePermission):
    """
    Permission to check if the user is an admin of the company they're trying to modify.
    """
    def has_object_permission(self, request, view, obj):
        # Check if the user has an employer profile linked to this company
        if hasattr(request.user, 'employer_profile'):
            return (
                request.user.employer_profile.company == obj and
                request.user.employer_profile.is_company_admin
            )
        return False

class IsCompanyMember(permissions.BasePermission):
    """
    Permission to check if the user is associated with the company (any role).
    """
    def has_object_permission(self, request, view, obj):
        if hasattr(request.user, 'employer_profile'):
            return request.user.employer_profile.company == obj
        return False
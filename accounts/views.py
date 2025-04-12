from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.shortcuts import redirect

class CustomLoginView(LoginView):
    """
    Custom login view that validates the user's role and redirects them
    to their respective dashboard after login.
    """
    def form_valid(self, form):
        # Authenticate the user
        user = form.get_user()

        # Get the expected role from the query parameter
        expected_role = self.request.GET.get('role')

        # Check if the user's role matches the expected role
        if expected_role and user.role != expected_role:
            messages.error(self.request, f"You are not authorized to access the {expected_role.capitalize()} Portal.")
            return redirect('login')  # Redirect back to the login page

        # Prevent admins from logging in through the frontend portals
        if user.role == 'admin':
            messages.error(self.request, "Admins cannot log in through the frontend portals.")
            return redirect('login')  # Redirect back to the login page

        # If roles match, proceed with login
        return super().form_valid(form)

    def get_success_url(self):
        # Redirect to the 'next' parameter or the user's default dashboard
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url

        # Default redirection based on role
        user = self.request.user
        if user.role == 'gatekeeper':
            return '/gatekeeper/dashboard/'
        elif user.role == 'teacher':
            return '/teacher/dashboard/'
        elif user.role == 'registrar':
            return '/registrar/dashboard/'
        elif user.role == 'finance':
            return '/finance/dashboard/'
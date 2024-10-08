from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
import json
from django.contrib.auth.models import User
from validate_email import validate_email
from django.contrib import messages
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes, force_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from .utils import token_generator
from django.contrib import auth

# Create your views here.

class UsernameValidationView(View): 
    def post(self, request):
        data = json.loads(request.body)
        username = data['username']

        if not str(username).isalnum():
            return JsonResponse({'username_error': 'username should only contain alphanumeric characters'}, status=400)
        if User.objects.filter(username=username).exists():
            return JsonResponse({'username_error': 'username in use, choose another one'}, status=409)
        
        return JsonResponse({'username_valid': True})
    

class EmailValidationView(View): 
    def post(self, request):
        data = json.loads(request.body)
        email = data['email']

        if not validate_email(email):
            return JsonResponse({'email_error': 'email is Invalid'}, status=400)
        if User.objects.filter(email=email).exists():
            return JsonResponse({'email_error': 'email in use, choose another one'}, status=409)
        
        return JsonResponse({'email_valid': True})

    
class RegistrationView(View):     
    def get(self, request): 
        return render(request, 'sign-up.html')

    def post(self, request):
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        context = {
            'fieldValues': request.POST
        }

        if not User.objects.filter(username=username).exists():
            if not User.objects.filter(email=email).exists():
                if len(password) < 6:
                    messages.error(request, "Password too short")
                    return render(request, 'sign-up.html', context)


                user = User.objects.create_user(username=username, email=email)
                user.set_password(password)
                user.is_active = False
                user.save()

                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                domain = get_current_site(request).domain
                link = reverse("activate", kwargs={'uidb64': uidb64, 'token': token_generator.make_token(user)})
                activate_url = "http://"+domain+link

                email_subject = "Activate your account"
                email_body = "Hi "+user.username + ", please click this link to activate your account\n" + activate_url
                email = EmailMessage(
                    email_subject, 
                    email_body,
                    'noreply@semycolon.com',
                    [email],
                )
                email.send(fail_silently=False)

                messages.success(request, "Account successfully created")
                return render(request, 'sign-up.html')

        return render(request, 'sign-up.html')

class VerificationView(View):
    def get(self, request, uidb64, token):

        try: 
            id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=id)

            if not token_generator.check_token(user, token):
                return redirect('sign-in' + "?message=" + "User already activated")

            if user.is_active:
                return redirect('sign-in')
            user.is_active=True
            user.save()

            messages.success(request, "Account activated successfully")

        except Exception as ex:
            pass
        
        return redirect('sign-in')

class LoginView(View): 
    def get(self, request):
        return render(request, 'sign-in.html')

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']

        if username and password:
            user = auth.authenticate(username = username, password = password)
            if user:
                if user.is_active:
                    auth.login(request, user)
                    messages.success(request, "Welcome, " + user.username + ", you are now logged in.")
                    return redirect("dashboard")
                else:
                    messages.error(request, "Account is not active, please check your email for activation link")
                    return render(request, 'sign-in.html') 
            else:
                messages.error(request, "Invalid credentials, please try again")
                return render(request, 'sign-in.html') 
        else:
            messages.error(request, "Please fill all fields")
            return render(request, 'sign-in.html') 
        
class LogoutView(View):
    def post(self, request):
        auth.logout(request)
        messages.success(request, "You have been logged out.")
        return redirect('sign-in')
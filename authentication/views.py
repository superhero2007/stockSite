from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect

from django.http import HttpResponseRedirect

def login_view(request):
    context = {}
    redirect_url = request.POST.get('next',
                       request.GET.get('next', 
                            '/Semanteon/Signals'))
    context['next'] = redirect_url

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:
            # the password verified for the user
            if user.is_active:
                login(request, user)
                # return HttpResponseRedirect(redirect_url)
                print("redirecting: " + str(redirect_url))
                return redirect(redirect_url)
                #TODO: redirect to the correct page after authentication
                # return redirect('/ticker')
            else:
                print("The password is valid, but the account has been disabled!")
        else:
            # the authentication system was unable to verify the username and password
            context['login_error'] = "The username and password were incorrect."

    return render(request, 'authentication/login.html', context)

def logout_view(request):
    logout(request)
    return redirect('index')


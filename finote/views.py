from django.shortcuts import render, redirect

def home(request):
    if request.user.is_authenticated:
        return redirect('home:home_feed') 
    return render(request, 'home.html')

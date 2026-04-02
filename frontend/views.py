from django.shortcuts import render

def home_view(request):
    return render(request, 'frontend/index.html')

def about_view(request):
    return render(request, 'frontend/about.html')

def contact_view(request):
    return render(request, 'frontend/contact.html')
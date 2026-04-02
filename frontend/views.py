from django.shortcuts import render

def home_view(request):
    return render(request, 'frontend/index.html')
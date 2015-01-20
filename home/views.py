from django.shortcuts import render


def index(request):
    return render(request, 'home/index.html')


def about(request):
    return render(request, 'home/about.html')


def impressum(request):
    return render(request, 'home/impressum.html')

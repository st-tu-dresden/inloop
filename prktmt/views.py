from django.shortcuts import render_to_response


def handler404(request):
    return render_to_response('404.html')


def handler500(request):
    return render_to_response('500.html')

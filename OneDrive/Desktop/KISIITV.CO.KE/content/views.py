from django.shortcuts import render

def home(request):
    """
    Renders the main Kisii TV homepage.
    """
    return render(request, 'index.html')
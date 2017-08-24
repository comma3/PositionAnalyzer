# Create your views here.
from django.shortcuts import render_to_response
from django.shortcuts import render


def show_about(request):
    return render(request, 'about/about.html')

   
def show_contact(request):
    return render(request, 'contact/contact.html')
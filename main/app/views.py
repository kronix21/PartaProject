from django.template.response import TemplateResponse

def index(request):
    return TemplateResponse(request, 'index.html')

def equipment(request):
    return TemplateResponse(request, 'equipment.html')

def add_equipment(request):
    return TemplateResponse(request, 'add_equipment.html')

def catalog(request):
    return TemplateResponse(request, 'catalog.html')

def edit(request):
    return TemplateResponse(request, 'edit.html')

def profile(request):
    return TemplateResponse(request, 'profile.html')

def repairs(request):
    return TemplateResponse(request, 'repairs.html')

def signin_staff(request):
    return TemplateResponse(request, 'signin_staff.html')

def signin(request):
    return TemplateResponse(request, 'signin.html')

def signup_staff(request):
    return TemplateResponse(request, 'signup_staff.html')

def signup(request):
    return TemplateResponse(request, 'signup.html')

def statement(request):
    return TemplateResponse(request, 'statement.html')
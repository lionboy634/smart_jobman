from django.contrib import auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.template.loader import get_template, render_to_string
from django.template import Context
from django.shortcuts import render, redirect , get_object_or_404
from django.urls import reverse, reverse_lazy
from dashboard.tasks import send_email
from account.forms import *
from jobapp.permission import user_is_employee 
from jobmanp.views import handle_uploaded_file
from jobapp.models import *
import textract as tx


def get_success_url(request):

    """
    Handle Success Url After LogIN

    """
    if 'next' in request.GET and request.GET['next'] != '':
        return request.GET['next']
    else:
        return reverse('jobapp:home')



def employee_registration(request):
    """ Handle Employee Registration """
    form = EmployeeRegistrationForm(request.POST or None)
    if form.is_valid():
        form = form.save()
        return redirect('account:login')
    context={
        
            'form':form
        }

    return render(request,'account/employee-registration.html',context)


def employer_registration(request):
    """ view handling employer registration """

    form = EmployerRegistrationForm(request.POST or None)
    if form.is_valid():
        mto = request.POST.get("email")
        print(mto)
        mt = "rexilinbrown1@gmail.com"
        subject = "WELCOME TO JOBMAN"
        msg = render_to_string("jobapp/welcome.html")
        send_email.delay(mto, subject, msg)
        form = form.save()
        
        return redirect('account:login')
    context={
        
            'form':form
        }

    return render(request,'account/employer-registration.html',context)


@login_required(login_url=reverse_lazy('accounts:login'))
@user_is_employee
def employee_edit_profile(request, id=id):

    """
    Handle Employee Profile Update Functionality
    """
    user = get_object_or_404(User, id=id)
    print(request.user.resume_title)
    form = EmployeeProfileEditForm(request.POST or None, request.FILES, instance=user)
    if "resume" in request.FILES:

            handle_uploaded_file(
                    request.FILES["resume"], request.FILES["resume"].name
                )
    if form.is_valid():
        filename = "resume/" + request.FILES["resume"].name
        resume_content = tx.process(filename, encoding='ascii')
        resume_content = str(resume_content, 'utf-8')
        user.resume_title = request.FILES["resume"].name
        user.resume_text = resume_content
        user.save()
        form = form.save()
        messages.success(request, 'Your Profile Was Successfully Updated!')
        return redirect(reverse("account:edit-profile", kwargs={
                                    'id': form.id
                                    }))
    context={
        
            'form':form,
            'skills': Skill.objects.all()
        }

    return render(request,'account/employee-edit-profile.html',context)



def user_logIn(request):

    """
    Provides users to logIn

    """

    form = UserLoginForm(request.POST or None)
    

    if request.user.is_authenticated:
        return redirect('/')
    
    else:
        if request.method == 'POST':
            #form is authenticated
            if form.is_valid():
                auth.login(request, form.get_user())
                return HttpResponseRedirect(get_success_url(request))
    context = {
        'form': form,
    }

    return render(request,'account/login.html',context)


def user_logOut(request):
    #logout of the system
    auth.logout(request)
    messages.success(request, 'You are Successfully logged out')
    return redirect('account:login')
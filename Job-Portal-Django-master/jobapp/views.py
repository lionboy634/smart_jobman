
import json
import requests
from time import time
import jwt
import datetime

import pandas as pd
import textract as tx

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.urls import reverse, reverse_lazy
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.core.serializers import serialize
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail

from account.models import User
from jobapp.forms import *
from jobapp.models import *
from jobapp.permission import *
from jobmanp.views import *
from dashboard.tasks import test_func, send_email
from jobmanp.views import nlp_wrapper, Cleaner, extract_skills

User = get_user_model()

API_KEY = "api_key"
API_SEC = "api_sc"

def recommended_jobs():
    final_jobs = pd.read_csv("final_jobs.csv")
    resume = f"resume/AJAY CHINNI.docx"
    resume_data = tx.process(resume, encoding='ascii')
    resume_data = str(resume_data)
    resume_data = " ".join(Cleaner(resume_data)[2])
    resume_data = nlp_wrapper(resume_data)
    
    score = []
    for job in final_jobs['pos_desc_loc_jt_cmpname']:
        job = " ".join(Cleaner(job)[2])
        job = nlp_wrapper(job)
        score.append(job.similarity(resume_data))

    final_jobs['score'] = score
    final_jobs = final_jobs.sort_values(by='score', ascending=False)

    
    return final_jobs[:6]

    

def home_view(request):

    published_jobs = Job.objects.filter(is_published=True).order_by('-timestamp')
    jobs = published_jobs.filter(is_closed=False)
    news = News.objects.all()[:6]
    total_candidates = User.objects.filter(role='employee').count()
    total_companies = User.objects.filter(role='employer').count()
    paginator = Paginator(jobs, 4)
    page_number = request.GET.get('page',None)
    page_obj = paginator.get_page(page_number)
    if request.method=="POST":
        job_lists=[]
        job_objects_list = page_obj.object_list.values()
        for job_list in job_objects_list:
            job_lists.append(job_list)
        

        next_page_number = None
        if page_obj.has_next():
            next_page_number = page_obj.next_page_number()

        prev_page_number = None       
        if page_obj.has_previous():
            prev_page_number = page_obj.previous_page_number()

        data={
            'job_lists':job_lists,
            'current_page_no':page_obj.number,
            'next_page_number':next_page_number,
            'no_of_page':paginator.num_pages,
            'prev_page_number':prev_page_number
            
        }    
        return JsonResponse(data)
    
    context = {

    'total_candidates': total_candidates,
    'total_companies': total_companies,
    'total_jobs': len(jobs),
    'total_completed_jobs':len(published_jobs.filter(is_closed=True)),
    'page_obj': page_obj,
    'news' : news,
    'recommended_jobs' : recommended_jobs()
    }
    value = test_func.delay()
    print(type(value.get()))
    #send_email.delay()
    return render(request, 'jobapp/index.html', context)



def upload_resume(request):
    print(request.POST)
    if "resume" in request.FILES:

        fo = request.FILES['resume']
        content_type = fo.content_type
        print(content_type)
        sup_types = [
            "application/pdf",
            "application/rtf",
            "application/docx",
            "application/x-rtf",
            "application/ms-word",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.oasis.opendocument.text",
            "application/x-vnd.oasis.opendocument.text"
        ]
        if str(content_type) in sup_types:
            handle_uploaded_file(
                        request.FILES["resume"], request.FILES["resume"].name
                    )
            filename = "resume/" + request.FILES["resume"].name
            resume_content = tx.process(filename, encoding='ascii')
            resume_content = str(resume_content, 'utf-8')
            skills = extract_skills(resume_content)
            user = request.user
            user.resume_title = request.FILES["resume"].name
            user.skills = skills
            user.resume_text = resume_content
            user.save()
            messages.success(request, 'Your Profile Was Successfully Updated!')
            return render(request,'account/employee-edit-profile.html',{"error" : "uploaded successfully"})

        else:
            return render(request,'account/employee-edit-profile.html',{"error" : "file type not supported"})



def company_view(request):
    company = User.objects.filter(role="employer")
    return render(request, 'jobapp/company.html',{
        "companies" : company
    }
    )



def review(request, id):
    company = User.objects.get(id=id)
    print(company)
    job = Job.objects.filter(user=company)
    print(job)
    return render(request, 'jobapp/review.html',{
        "company" : company
    })



def edit_personalinfo(request):
    if request.method == "POST":
        validate_form = PersonalInfoForm(request.POST, instance=request.user)
        if validate_form.is_valid():
            user = validate_form.save(commit=False)

            user.first_name = request.POST.get("first_name")
            user.last_name = request.POST.get("last_name")
            user.mobile = (
                request.POST.get("mobile")
                if request.POST.get("mobile")
                else None
            )
            if request.POST.get("email"):
                user.email = request.POST.get("email")
            if request.POST.get("current_city"):
                user.current_city = request.POST.get("current_city")
            user.profile_updated = datetime.datetime.now(timezone.utc)
            user.save()
            return render(request,'account/employee-edit-profile.html',{"message" : "updated successfully"})
        else:
            return render(request,'account/employee-edit-profile.html',{"message" : "couldnt update profile"})

def news_list_view(request, id):
    news = News.objects.get(id=id)
    
    context = {
        'news' : news
    }
    return render(request, 'jobapp/news.html', context)



def job_list_View(request):
    """

    """
    job_list = Job.objects.filter(is_published=True,is_closed=False).order_by('-timestamp')
    paginator = Paginator(job_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {

        'page_obj': page_obj,

    }
    return render(request, 'jobapp/job-list.html', context)


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def create_job_View(request):
    """
    Provide the ability to create job post
    """
    form = JobForm(request.POST or None)

    user = get_object_or_404(User, id=request.user.id)
    categories = Category.objects.all()

    if request.method == 'POST':

        if form.is_valid():

            instance = form.save(commit=False)
            instance.user = user
            instance.is_published = True
            instance.save()
            # for save tags
            form.save_m2m()
            messages.success(
                    request, 'You are successfully posted your job! Please wait for review.')
            return redirect(reverse("jobapp:single-job", kwargs={
                                    'id': instance.id
                                    }))

    context = {
        'form': form,
        'categories': categories
    }
    return render(request, 'jobapp/post-job.html', context)


def single_job_view(request, id):
    """
    Provide the ability to view job details
    """

    job = get_object_or_404(Job, id=id)
    related_job_list = job.tags.similar_objects()

    paginator = Paginator(related_job_list, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'job': job,
        'page_obj': page_obj,
        'total': len(related_job_list)

    }
    return render(request, 'jobapp/job-single.html', context)


def search_result_view(request):
    """
        User can search job with multiple fields

    """

    job_list = Job.objects.order_by('-timestamp')

    # Keywords
    if 'job_title_or_company_name' in request.GET:
        job_title_or_company_name = request.GET['job_title_or_company_name']

        if job_title_or_company_name:
            job_list = job_list.filter(title__icontains=job_title_or_company_name) | job_list.filter(
                company_name__icontains=job_title_or_company_name)

    # location
    if 'location' in request.GET:
        location = request.GET['location']
        if location:
            job_list = job_list.filter(location__icontains=location)

    # Job Type
    if 'job_type' in request.GET:
        job_type = request.GET['job_type']
        if job_type:
            job_list = job_list.filter(job_type__iexact=job_type)

    # job_title_or_company_name = request.GET.get('text')
    # location = request.GET.get('location')
    # job_type = request.GET.get('type')

    #     job_list = Job.objects.all()
    #     job_list = job_list.filter(
    #         Q(job_type__iexact=job_type) |
    #         Q(title__icontains=job_title_or_company_name) |
    #         Q(location__icontains=location)
    #     ).distinct()

    # job_list = Job.objects.filter(job_type__iexact=job_type) | Job.objects.filter(
    #     location__icontains=location) | Job.objects.filter(title__icontains=text) | Job.objects.filter(company_name__icontains=text)

    paginator = Paginator(job_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {

        'page_obj': page_obj,

    }
    return render(request, 'jobapp/result.html', context)


def recruit_search_view(request):
    if request.method == "POST":
        print(request.POST.get("skill"))
        if 'skill' in request.POST:
            skill = request.POST['skill']
        
        if 'location' in request.POST:
            location = request.POST['location']
        
        user = User.objects.filter(skills__in=skill)
        if user:
            print("userss")
        else:
            print("no userrrrss")
        


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employee
def apply_job_view(request, id):

    form = JobApplyForm(request.POST or None)

    user = get_object_or_404(User, id=request.user.id)
    applicant = Applicant.objects.filter(user=user, job=id)

    if not applicant:
        if request.method == 'POST':

            if form.is_valid():
                instance = form.save(commit=False)
                instance.user = user
                instance.save()

                messages.success(
                    request, 'You have successfully applied for this job!')
                return redirect(reverse("jobapp:single-job", kwargs={
                    'id': id
                }))

        else:
            return redirect(reverse("jobapp:single-job", kwargs={
                'id': id
            }))

    else:

        messages.error(request, 'You already applied for the Job!')

        return redirect(reverse("jobapp:single-job", kwargs={
            'id': id
        }))


@login_required(login_url=reverse_lazy('account:login'))
def dashboard_view(request):
    """
    """
    jobs = []
    savedjobs = []
    appliedjobs = []
    total_applicants = {}
    if request.user.role == 'employer':

        jobs = Job.objects.filter(user=request.user.id)
        for job in jobs:
            count = Applicant.objects.filter(job=job.id).count()
            total_applicants[job.id] = count

    if request.user.role == 'employee':
        savedjobs = BookmarkJob.objects.filter(user=request.user.id)
        appliedjobs = Applicant.objects.filter(user=request.user.id)
    context = {

        'jobs': jobs,
        'savedjobs': savedjobs,
        'appliedjobs':appliedjobs,
        'total_applicants': total_applicants
    }

    return render(request, 'jobapp/dashboard.html', context)


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def delete_job_view(request, id):

    job = get_object_or_404(Job, id=id, user=request.user.id)

    if job:

        job.delete()
        messages.success(request, 'Your Job Post was successfully deleted!')

    return redirect('jobapp:dashboard')


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def make_complete_job_view(request, id):
    job = get_object_or_404(Job, id=id, user=request.user.id)

    if job:
        try:
            job.is_closed = True
            job.save()
            messages.success(request, 'Your Job was marked closed!')
        except:
            messages.success(request, 'Something went wrong !')
            
    return redirect('jobapp:dashboard')



@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def all_applicants_view(request, id):

    all_applicants = Applicant.objects.filter(job=id)

    context = {

        'all_applicants': all_applicants
    }

    return render(request, 'jobapp/all-applicants.html', context)


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employee
def delete_bookmark_view(request, id):

    job = get_object_or_404(BookmarkJob, id=id, user=request.user.id)

    if job:

        job.delete()
        messages.success(request, 'Saved Job was successfully deleted!')

    return redirect('jobapp:dashboard')


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def applicant_details_view(request, id):

    user = get_object_or_404(User, id=id)
    

    context = {

        'applicant': user
    }
    
    return render(request, 'jobapp/applicant-details.html', context)


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employee
def job_bookmark_view(request, id):

    form = JobBookmarkForm(request.POST or None)

    user = get_object_or_404(User, id=request.user.id)
    applicant = BookmarkJob.objects.filter(user=request.user.id, job=id)

    if not applicant:
        if request.method == 'POST':

            if form.is_valid():
                instance = form.save(commit=False)
                instance.user = user
                instance.save()

                messages.success(
                    request, 'You have successfully save this job!')
                return redirect(reverse("jobapp:single-job", kwargs={
                    'id': id
                }))

        else:
            return redirect(reverse("jobapp:single-job", kwargs={
                'id': id
            }))

    else:
        messages.error(request, 'You already saved this Job!')

        return redirect(reverse("jobapp:single-job", kwargs={
            'id': id
        }))


@login_required(login_url=reverse_lazy('account:login'))
@user_is_employer
def job_edit_view(request, id=id):
    #HANDLES JOB UPDATE

    job = get_object_or_404(Job, id=id, user=request.user.id)
    categories = Category.objects.all()
    form = JobEditForm(request.POST or None, instance=job)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.save()
        # for save tags
        # form.save_m2m()
        messages.success(request, 'Your Job Post Was Successfully Updated!')
        return redirect(reverse("jobapp:single-job", kwargs={
            'id': instance.id
        }))
    context = {

        'form': form,
        'categories': categories
    }

    return render(request, 'jobapp/job-edit.html', context)



def job_alert(request):
    if request.method == "GET":
        template = "jobapp/job_alert.html"
        if request.user.is_authenticated:
            alert = JobAlert.objects.filter(email=request.user.email)
        else:
            alert = []
        print
        return render(
            request,
            template,
            {
                "skills" : Skill.objects.all(),
                "alerts" : alert
                

            }
        )
    
    
    validate_jobalert = JobAlertForm(request.POST)
    if validate_jobalert.is_valid():
        job_alert = JobAlert.objects.create(name=request.POST.get("name"))
        if request.POST.get("min_salary"):
            job_alert.min_salary = request.POST.get("min_salary", "")
            job_alert.max_salary = request.POST.get("max_salary", "")
        
        if request.POST.getlist("skill"):
            job_alert.skill.add(*request.POST.getlist("skill"))
        job_alert.role = request.POST.get("role", "")
        job_alert.email = (
            request.user.email 
            if request.user.is_authenticated
            else request.POST.get("email", "")
        )

        while True:
            unsubscribe = get_random_string(length=15)
            if not JobAlert.objects.filter(unsubscribe_code__iexact=unsubscribe):
                break
        job_alert.unsubscribe_code = unsubscribe

        while True:
            subscribe = get_random_string(length=15)
            if not JobAlert.objects.filter(subscribe_code__iexact=subscribe):
                break
        job_alert.subscribe_code = subscribe
        job_alert.save()
        #send a message
        return HttpResponse(
            json.dumps({
                "message": "job alert created successfully",
                "error" : False, 
                "alert_id": job_alert.id

            })
        )

    else:
        return HttpResponse(
            json.dumps({
                "error": True, 
                "message": validate_jobalert.errors

            })
        )
        



def job_alert_results(request, alert_id):
    if request.user.is_authenticated and request.user.role == "employee":
        job_alert = JobAlert.objects.filter(id=alert_id, email=request.user.email)
    else:
        job_alert = JobAlert.objects.filter(id=alert_id)

    
    if request.user.is_authenticated:
        if request.user.is_recruiter or request.user.role == "employer":
            template = "404.html"
            message = "SORRY NO JOB ALERT AVAILABLE"
            return render(request, template, {"message": message}, status=404)

    if job_alert:
        job_alert = job_alert[0]
        skills = []
        for skill in job_alert.skill.values():
            skills.append(skill.get("name"))
        print(skills)
        jobs_list = Job.objects.filter(
            Q(tags__name__in=skills) &
            (
                Q(title__icontains = job_alert.role)
                | Q(salary = job_alert.max_salary)
                | Q(salary = job_alert.min_salary)
            )
            
        ).distinct()

        if not jobs_list:
            jobs_list = Job.objects.filter(
                is_published=True, tags__name__in=skills
            ).distinct()
        
        data = {
            "job_alert" : job_alert,
            "jobs_list" : jobs_list
        }
        print(data)
        return render(request, "jobapp/job_alert_result.html", data)

    
    else:
        return render(request, "jobapp/job_alert_result.html", {
            "job_alert" : []
        })


    
    


def generate_token():
    token = jwt.encode(
        {"iss" : settings.API_KEY , "exp": time() + 500},
        settings.API_SEC ,

        algorithm='HS256'
    )
    return token


meeting_details = {
    "topic" : "JOB INTERVIEW",
    "type" : 2,
    "start_time" : "2022-09-14T10: 10 : 57",
    "duration" : 45, 
    "timezone" : "Africa/Accra",
    "agenda" : "test",
    "recurrence": {
        "type" : 1,
        "repeat_interval" : 1
    },
    "settings":{
        "host_video" : "true",
        "participant_video" : "true"
    } 
}

def create_meeting(request):
    if request.method == "POST":
        headers = {'authorization' : 'Bearer ' + generate_token(), 'content-type' : 'application/json'}
        r = requests.post(f'https://api.zoom.us/v2/users/me/meetings' , headers=headers, data = json.dumps(meeting_details))
        print("creating zoom meeting ")
        res = json.loads(r.text)
        join_url = res['join_url']
        print(request.user.email)
        meeting_password = res['password']
        subject = "INTERVIEW SCHEDULED"
        message = 'your meeting has been scheduled'
        email = request.POST.get("email")
        #email_from = "poseidon.brown@protonmail.com"
        #recipient_list = ['rexilinbrown1@gmail.com',] 
        mto = [email]
        send_email.delay(mto, subject, message)
        return HttpResponse(
            json.dumps({
                "message" : "interview created successfully",
                "data" : join_url
            })
        )
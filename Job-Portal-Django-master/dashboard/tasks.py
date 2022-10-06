import os
import re
import json
import datetime
from datetime import datetime, timedelta
import requests
from django.shortcuts import render
from jobapp.models import Job, JobAlert
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.core.mail import send_mail
from django.template import Template, Context, loader
from django.utils.html import strip_tags
from django.conf import settings
from job.celery import app
from django.conf import settings
import pandas as pd
from celery import shared_task
from django.conf import settings
from jobmanp.views import Cleaner, get_cleaned_words, read_resume, nlp_wrapper
from jobapp.models import SearchResult, Skill


#nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.tokenize import word_tokenize
import textdistance as td

@shared_task(bind=True)
def test_func(self):
    value = []
    for i in range(10):
        print(i)
        value.append(i)
    return value


#function finds jobs that match the resumes of candidates
@shared_task(bind=True)
def finder(self, resume_text):
    final_jobs = pd.read_csv("final_job.csv")
    if resume_text is not None:
        resume_data = str(resume_text)
        resume_data = " ".join(Cleaner(resume_data)[2])
        resume_data = nlp_wrapper(resume_data)
            
        score = []
        for job in final_jobs['pos_desc_loc_jt_cmpname']:
            job = " ".join(Cleaner(job)[2])
            job = nlp_wrapper(job)
            score.append(resume_data.similarity(job))

        final_jobs['score'] = score
        final_jobs = final_jobs.sort_values(by='score', ascending=False)
        #final_jobs = final_jobs[:5]
        final_jobs = final_jobs[final_jobs['score'] > 0.6 ][:5]
        return final_jobs.values.tolist()
    else:
        return [""]
   

"""
how the similarity is computed
cosine similarity: measures the proximity of the documents in the vector space
jaccard similarity: measures similarity by finding the intersection of common words between the documents divided by the size of the union of sample sets 
sorenson dice similarity: the coefficient may be defined as twice the shared information (intersection) over the sum of cardinalities

"""


#function computes the similarity between job description and all resumes of candidates in the system
@shared_task(bind=True)
def recommend_job(self, job_desc):
    if job_desc is not None:
        df = pd.read_csv("job_seeker.csv")
        job_desc = str(job_desc)
        job_desc = job_desc.replace("\n", " ")
        job_desc = job_desc.replace("\t", " ")
        job_desc = " ".join(Cleaner(job_desc)[2])
        scores = []
        for res_text in df['resume_text']:
            res_text = " ".join(Cleaner(res_text)[2])
            #compute cosine similarity between the two documents
            cos = td.cosine(job_desc, res_text)
            #computes the sorensons dice between the two documents
            soren = td.sorensen_dice(job_desc, res_text)
            #compute the jaccard cofficient between the two documents
            jac = td.jaccard(job_desc, res_text)
            over = td.overlap.normalized_similarity(job_desc, res_text)
            #compute the average score
            score = cos + soren + jac + over
            score = (score/4)
            #score is converted in percentage
            score = score * 100
            #scores.append(round((score / 4),3)) 
            scores.append(round(score,1))
        
        

        #pass score into score column
        df['score'] = scores
        df = df.sort_values(by='score', ascending=False)
        #new_df = df[df['score'] > 0.6][:10]
        df = df[df['score'] > 60 ][:10]
        return df.values.tolist()
    else:
        return [" "]




@app.task
def extract_news_data():
    headers = {'Authorization': 'b7de039e294740bb84d8dff8c2bbf97d'}
    query_params = {
        'q': "tesla",
        #'source' : "bbc-news",
        "sortBy" : "popularity", 
        "language" : "en",
        "apiKey": "893a256ebdbe4f15a008045c26f3cce5"
    }
    main_url = 'https://newsapi.org/v2/everything'
    response = requests.get(main_url, params=query_params)
    result = response.json()
    response_string = json.dumps(result, indent=4)
    response_dict = json.loads(response_string)
    articles = response_dict['articles'][:50]
    df = pd.read_json(json.dumps(articles))
    df.to_csv("news_data.csv")

    
#function that sends mail 
@app.task
def send_email(mto, msubject, mbody):
    if type(mto) != "list":
        #convert string into a list class
        mto = [mto]
    mail  = send_mail(msubject, strip_tags(mbody), settings.EMAIL_HOST_USER , mto, html_message=mbody, fail_silently=False)
    if mail:
        return "mail sent successfully"
    #mail.content_subtype = 'html'
    #mail.send()


#function that periodically updates job postings in the system
@shared_task(bind=True)
def update_job_data(self):
    job = Job.objects.all()
    qs = job.values()
    df = pd.DataFrame.from_records(qs)
    return df.to_csv("jobs.csv")



@shared_task(bind=True)
def update_jobseeker_data(self):
    job = Job.objects.filter(role="employee")
    qs = job.values()
    df = pd.DataFrame.from_records(qs)
    return df.to_csv("job_seeker.csv")





#function that returns a cleaned data
@app.task
def clean_job_data():
    stop = stopwords.words("english")
    df = pd.read_csv("jobs.csv")
    #subsetting columns
    col_list = list(['id'] + ['title'] + ['description'] + ['location'] + ['job_type'] + ['salary'] + ['company_name'])
    df = df[col_list]
    #remove stopwords
    df['pos_desc_loc_jt_cmpname'] = df['title'].map(str) + " " + df['description'] + " "  + df['company_name']
    #remove html tags
    df['pos_desc_loc_jt_cmpname'] = df['pos_desc_loc_jt_cmpname'].str.replace("<[^<>]*>", " ", regex=True)
    df['pos_desc_loc_jt_cmpname'] = df['pos_desc_loc_jt_cmpname'].str.replace("^[a-zA-Z \n\.]", " ", regex=True)
    df['pos_desc_loc_jt_cmpname'] = df['pos_desc_loc_jt_cmpname'].str.lower()
    
    #remove stopwords
    df['pos_desc_loc_jt_cmpname'].apply(lambda x: ' '.join([word for word in x.split() if word not in (stop)]))
    df['pos_desc_loc_jt_cmpname'].apply(lambda x: filter(None, x.split(" ")))
    #instantiate lemmatizer
    lemmatizer = WordNetLemmatizer()
    df['pos_desc_loc_jt_cmpname'].apply(lambda x: ' '.join([lemmatizer.lemmatize(word) for word in x]))
    df['pos_desc_loc_jt_cmpname'].apply(lambda x: ' '.join(x))
    #return the cleaned jobs.csv
    df.to_csv("final_job.csv")
    





resume_dir = "resume/"
resume_names = os.listdir(resume_dir)
@app.task
def get_resume_data():
    document = read_resume(resume_names, resume_dir)
    Doc = get_cleaned_words(document)
    df = pd.DataFrame(Doc)
    return df.to_csv("resumes.csv", index=False)


@app.task
def edit_job_dataset():
    df = pd.read_csv("jobs.csv")




#Function emails jobs to users based on job alerts they have applied
@app.task
def alert_to_users():
    from_date = datetime.now() - timedelta(days=1)
    to_date = datetime.now()
    #get job posting posted today
    job_post = Job.objects.filter(
        timestamp__range = (from_date, to_date), is_published=True
    )
    user = get_user_model()
    users = user.objects.filter(role="employee")
    for job_user in users:
        skills = job_user.skills
        user_skills = []
        user_location = job_user.current_city
        if skills and user_location:
            pattern = r'[^a-zA-z0-9\s]'
            skills = skills.replace("[", " ")
            skills = skills.replace("]", " ")
            skills = skills.split(",")
            for skill in skills:
                skill = re.sub(pattern, " ", skill)
                user_skills.append(skill.strip())
        job = job_post.filter(Q(tags__name__in=user_skills) | Q(location=user_location))
        t = loader.get_template("jobapp/alerts.html")
        c = { "jobposts" : job.distinct()[:10], "user" : job_user }
        subject = "JOB ALERT FOR TOP MATCHING JOBS"
        rendered = t.render(c)
        mto = job_user.email
        send_email.delay(mto, subject, rendered)



#function records the search activity of jobseekers
@app.task
def save_search_results(user, ip_address, skill , location, job_type):
    #call the user model
    User = get_user_model()
    user = User.objects.filter(id=user).first()
    search_result = SearchResult.objects.create(ip_address=ip_address)
    if skill:
        search_result.skill = skill
    if location:
        search_result.location = location
    if job_type:
        search_result.job_type = job_type
    
    if user:
        search_result.user = user
    saved = search_result.save()
    if saved:
        return "saved"
    else:
        return "couldnt save it"

            


@app.task
def jobs_based_on_activity():
    User = get_user_model()
    users = User.objects.filter(role="employee")
    for user in users:
        search_results = SearchResult.objects.filter(user=user)
        for result in search_results:
            location = result.location
            job_type = result.job_type
            skill = result.skill
            if job_type or skill:
                job_list = Job.objects.filter(
                    Q(tags__name__in=skill) |
                (
                    Q(job_type = job_type)
                )
                )
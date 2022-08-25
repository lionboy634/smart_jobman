import os
import json
import requests
from django.shortcuts import render
from jobapp.models import Job
from django.core.mail import EmailMessage
from job.celery import app
from django.conf import settings
import pandas as pd
from celery import shared_task
from django.conf import settings
from jobmanp.views import Cleaner, get_cleaned_words, read_resume


#nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.tokenize import word_tokenize
@shared_task(bind=True)
def test_func(self):
    for i in range(10):
        print(i)
    return "done"



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

    

@app.task
def send_email(mto, msubject, mbody):
    if type(mto) != "list":
        mto = [mto]
    mail  = EmailMessage(msubject, mbody, 'django.conf.settings.DEFAULT_FROM_EMAIL', mto)
    mail.content_subtype = 'html'
    mail.send()



@shared_task(bind=True)
def update_job_data(self):
    job = Job.objects.all()
    qs = job.values()
    df = pd.DataFrame.from_records(qs)
    return df.to_csv("jobs.csv")



@app.task
def clean_job_data():
    stop = stopwords.words("english")
    df = pd.read_csv("jobs.csv")
    #subsetting columns
    col_list = list(['id'] + ['title'] + ['description'] + ['location'] + ['job_type'] + ['salary'] + ['company_name'])
    df = df[col_list]
    #remove stopwords
    df['pos_desc_loc_jt_cmpname'] = df['title'].map(str) + " " + df['description'] + " "  + df['company_name']
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





@app.task
def alert_to_users():
    pass
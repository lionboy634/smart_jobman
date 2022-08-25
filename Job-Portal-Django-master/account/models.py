from distutils.command.upload import upload
from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import datetime
from django.utils.timezone import now
from account.managers import CustomUserManager
from django.conf import settings

import textract as tx
import pandas as pd
from jobmanp.views import nlp_wrapper, Cleaner  

GENDER_TYPE = (
    ('M', "Male"),
    ('F', "Female"),
    ("O", "Others"),
    ("N/A", "Prefer not talk")

)

ROLE = (
    ('employer', "Employer"),
    ('employee', "Employee"),
)

USER_TYPE = (
    ("JS", "jobseeker"),
    ("RA", "recruiter admin")
)

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True, blank=False,
                              error_messages={
                                  'unique': "A user with that email already exists.",
                              })
    role = models.CharField(choices=ROLE,  max_length=10)
    gender = models.CharField(choices=GENDER_TYPE, max_length=20)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    education = models.TextField(blank=True, null=True)
    profile_pic = models.FileField(upload_to=settings.MEDIA_ROOT, blank=True, null=True)
    employment_history = models.TextField(blank=True, null=True)
    current_city = models.CharField(max_length=2000, null=True, blank=True)
    permanent_address = models.TextField(max_length=2000, null=True, blank=True)
    preferred_city = models.CharField(max_length=1000, blank=True, null=True)
    resume_title = models.CharField(max_length=2000, blank=True, null=True)
    skills = models.CharField(max_length=2000, null=True, blank=True)
    resume_text = models.TextField(blank=True, null=True)
    profile_updated = models.DateTimeField(blank=True, default=now)
    profile_description = models.CharField(max_length=2000, blank=True, null=True)
    activation_code = models.CharField(max_length=100, null=True, blank=True)


    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.first_name+ ' ' + self.last_name


    @property
    def profile_completion_percentage(self):
        percent = 0
        if self.email:
            percent += 20
        if self.resume_text is not None:
            percent += 30
        if self.current_city is not None or self.permanent_address is not None:
            percent += 10
        if self.education is not None:
            percent += 10
        return percent


    @property
    def is_jobseeker(self):
        if self.role == "employee":
            return True
        return False

    @property
    def is_recruiter(self):
        if self.role == "employer":
            return True
        return False

    @property
    def recommended_jobs(self):
        final_jobs = pd.read_csv("final_jobs.csv")
        if self.resume_title is not None and self.resume_text is not None:
            resume_data = str(self.resume_text)
            resume_data = " ".join(Cleaner(resume_data)[2])
            resume_data = nlp_wrapper(resume_data)
            
            score = []
            for job in final_jobs['pos_desc_loc_jt_cmpname']:
                job = " ".join(Cleaner(job)[2])
                job = nlp_wrapper(job)
                score.append(resume_data.similarity(job))

            final_jobs['score'] = score
            final_jobs = final_jobs.sort_values(by='score', ascending=False)
            print(final_jobs)
            return final_jobs[:5]
        else:
            return [""]
   

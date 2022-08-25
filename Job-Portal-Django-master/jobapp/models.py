from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from jobmanp.views import Cleaner
User = get_user_model()
import spacy

try:
    nlp = spacy.load("en_core_web_md")

except:
    print("NLP model not found")


from ckeditor.fields import RichTextField
from taggit.managers import TaggableManager


JOB_TYPE = (
    ('1', "Full time"),
    ('2', "Part time"),
    ('3', "Internship"),
)

class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    

class Job(models.Model):

    user = models.ForeignKey(User, related_name='User', on_delete=models.CASCADE) 
    title = models.CharField(max_length=300)
    description = RichTextField()
    tags = TaggableManager()
    location = models.CharField(max_length=300)
    job_type = models.CharField(choices=JOB_TYPE, max_length=1)
    category = models.ForeignKey(Category,related_name='Category', on_delete=models.CASCADE)
    salary = models.CharField(max_length=30, blank=True)
    company_name = models.CharField(max_length=300)
    company_description = RichTextField(blank=True, null=True)
    url = models.URLField(max_length=200)
    last_date = models.DateField()
    is_published = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.title

 

class Applicant(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True, auto_now_add=False)


    def __str__(self):
        return self.job.title

    @property
    def resume_ranking(self):
        description = self.job.description
        job_title = self.job.title
        location = self.job.location
        resume_text = str(self.user.resume_text)
        desc_loc_title = str(job_title) + " " + str(location) + " " + str(description)
        desc_loc_title = " ".join(Cleaner(desc_loc_title)[2])
        resume_text = " ".join(Cleaner(resume_text)[2])
        print(desc_loc_title)
        description = nlp(desc_loc_title)
        resume_text = nlp(resume_text)
        scores  = description.similarity(resume_text)
        return int((scores  * 100) - 10 )

    

        
        


  

class BookmarkJob(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True, auto_now_add=False)


    def __str__(self):
        return self.job.title





class News(models.Model):
    source = models.CharField(max_length=1000, null=True, blank=True)
    author = models.CharField(max_length=1000, null=True, blank=True)
    url = models.CharField(max_length=1000, null=True, blank=True)
    imageurl = models.URLField(max_length=1000, null=True, blank=True)
    title = models.CharField(max_length=1000)
    description = models.TextField()
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now=True)



    def __str__(self):
        return self.title

STATUS = (
    ("Active", "Active"),
    ("InActive", "InActive"),
)

class Skill(models.Model):
    name = models.CharField(max_length=500)
    status = models.CharField(choices=STATUS, max_length=10)
    icon = models.CharField(max_length=1000)
    slug = models.SlugField(max_length=500, null=True, blank=True)
    meta_title = models.TextField(default="")
    meta_description = models.TextField(default="")
    page_content = models.TextField(default="")
    


    class Meta:
        ordering = ['name']


    def __str__(self):
        return self.name


    def save(self, *args, **kwargs):
        if self.slug is None:
            self.slug = self.name
        super().save(*args, **kwargs)


class JobAlert(models.Model):
    skill = models.ManyToManyField(Skill)
    location = models.CharField(max_length=1000)
    max_salary = models.IntegerField(null=True, blank=True)
    min_salary = models.IntegerField(null=True, blank=True)
    role = models.CharField(max_length=2000, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    name = models.CharField(max_length=2000, unique=True)
    unsubscribe_code = models.CharField(max_length=100, null=True, blank=True)
    is_unsubscribe = models.BooleanField(default=False)
    subscribe_code = models.CharField(max_length=100, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    unsubscribe_reason = models.TextField(default="")

    def __str__(self):
        return self.name

class Subscriber(models.Model):
    email = models.EmailField()
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    job_post = models.ForeignKey(
        Job, blank=True, null=True, on_delete=models.CASCADE
    )
    is_verified = models.BooleanField(default=False)
    unsubscribe_code = models.CharField(max_length=100, null=True, blank=True)
    is_unsubscribe = models.BooleanField(default=False)
    subscribe_code = models.CharField(max_length=100, null=True, blank=True)
    unsubscribe_reason = models.TextField(default="")

class DailySearchLog(models.Model):
    no_of_job_posts = models.IntegerField(default="0")
    skills = models.ForeignKey(Skill, on_delete=models.CASCADE)
    created_on = models.DateField()
    no_of_searches = models.IntegerField(default="0")
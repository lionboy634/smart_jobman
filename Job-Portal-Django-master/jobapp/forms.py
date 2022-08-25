import re

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib import auth

from jobapp.models import *
from ckeditor.widgets import CKEditorWidget



class JobForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        forms.ModelForm.__init__(self, *args, **kwargs)
        self.fields['title'].label = "Job Title :"
        self.fields['location'].label = "Job Location :"
        self.fields['salary'].label = "Salary :"
        self.fields['description'].label = "Job Description :"
        self.fields['tags'].label = "Tags :"
        self.fields['last_date'].label = "Submission Deadline :"
        self.fields['company_name'].label = "Company Name :"
        self.fields['url'].label = "Website :"


        self.fields['title'].widget.attrs.update(
            {
                'placeholder': 'eg : Software Developer',
            }
        )        
        self.fields['location'].widget.attrs.update(
            {
                'placeholder': 'eg : City',
            }
        )
        self.fields['salary'].widget.attrs.update(
            {
                'placeholder': 'GhS800 - GHS1200',
            }
        )
        self.fields['tags'].widget.attrs.update(
            {
                'placeholder': 'Use comma separated. eg: Python, JavaScript ',
            }
        )                        
        self.fields['last_date'].widget.attrs.update(
            {
                'placeholder': 'YYYY-MM-DD ',
                
            }
        )        
        self.fields['company_name'].widget.attrs.update(
            {
                'placeholder': 'Company Name',
            }
        )           
        self.fields['url'].widget.attrs.update(
            {
                'placeholder': 'https://example.com',
            }
        )    


    class Meta:
        model = Job

        fields = [
            "title",
            "location",
            "job_type",
            "category",
            "salary",
            "description",
            "tags",
            "last_date",
            "company_name",
            "company_description",
            "url"
            ]

    def clean_job_type(self):
        job_type = self.cleaned_data.get('job_type')

        if not job_type:
            raise forms.ValidationError("Service is required")
        return job_type

    def clean_category(self):
        category = self.cleaned_data.get('category')

        if not category:
            raise forms.ValidationError("category is required")
        return category


    def save(self, commit=True):
        job = super(JobForm, self).save(commit=False)
        if commit:
            
            job.save()
        return job




class JobApplyForm(forms.ModelForm):
    class Meta:
        model = Applicant
        fields = ['job']

class JobBookmarkForm(forms.ModelForm):
    class Meta:
        model = BookmarkJob
        fields = ['job']




class JobEditForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        forms.ModelForm.__init__(self, *args, **kwargs)
        self.fields['title'].label = "Job Title :"
        self.fields['location'].label = "Job Location :"
        self.fields['salary'].label = "Salary :"
        self.fields['description'].label = "Job Description :"
        # self.fields['tags'].label = "Tags :"
        self.fields['last_date'].label = "Dead Line :"
        self.fields['company_name'].label = "Company Name :"
        self.fields['url'].label = "Website :"


        self.fields['title'].widget.attrs.update(
            {
                'placeholder': 'eg : Software Developer',
            }
        )        
        self.fields['location'].widget.attrs.update(
            {
                'placeholder': 'eg : Accra',
            }
        )
        self.fields['salary'].widget.attrs.update(
            {
                'placeholder': 'Ghs800 - Ghs1200',
            }
        )
        # self.fields['tags'].widget.attrs.update(
        #     {
        #         'placeholder': 'Use comma separated. eg: Python, JavaScript ',
        #     }
        # )                        
        self.fields['last_date'].widget.attrs.update(
            {
                'placeholder': 'YYYY-MM-DD ',
            }
        )        
        self.fields['company_name'].widget.attrs.update(
            {
                'placeholder': 'Company Name',
            }
        )           
        self.fields['url'].widget.attrs.update(
            {
                'placeholder': 'https://example.com',
            }
        )    

    
        last_date = forms.CharField(widget=forms.TextInput(attrs={
                    'placeholder': 'Service Name',
                    'class' : 'datetimepicker1'
                }))

    class Meta:
        model = Job

        fields = [
            "title",
            "location",
            "job_type",
            "category",
            "salary",
            "description",
            "last_date",
            "company_name",
            "company_description",
            "url"
            ]

    def clean_job_type(self):
        job_type = self.cleaned_data.get('job_type')

        if not job_type:
            raise forms.ValidationError("Job Type is required")
        return job_type

    def clean_category(self):
        category = self.cleaned_data.get('category')

        if not category:
            raise forms.ValidationError("Category is required")
        return category


    def save(self, commit=True):
        job = super(JobEditForm, self).save(commit=False)
      
        if commit:
            job.save()
        return job


class PersonalInfoForm(forms.ModelForm):
    current_city = forms.CharField(max_length=50)
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30, required=False)
    marital_status = forms.CharField(max_length=30, required=False)
    
    class Meta:
        model = User
        fields = ["first_name", "mobile"]

    def __init__(self, *args, **kwargs):
        super(PersonalInfoForm, self).__init__(*args, **kwargs)
        self.fields["current_city"].required = True
        self.fields["current_city"].error_messages = {
            "required": "Current Location cannot be empty"
        }
        

    def clean_mobile(self):
        mobile = self.cleaned_data.get("mobile")
        if mobile:
            users = User.objects.filter(mobile=mobile).exclude(id=self.instance.id)
            if not users:
                length = len(str(mobile)) < 10 or len(str(mobile)) > 12
                symbols = bool(
                    re.search(r"[~\.,!@#\$%\^&\*\(\)_\{}\":;'\[\]]", mobile)
                ) or bool(re.search("[a-zA-Z]", mobile))
                if length or symbols:
                    raise forms.ValidationError("Please Enter Valid phone number")
                if length or symbols:
                    raise forms.ValidationError("Please Enter Valid phone number")
                else:
                    return mobile
            else:
                raise forms.ValidationError(
                    "User with this mobile number already exists"
                )

   






class JobAlertForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    min_salary = forms.IntegerField(required=False)
    max_salary = forms.IntegerField(required=False)

    class Meta:
        model = JobAlert
        fields = ["name", "skill", "role"]

    def __init__(self, *args, **kwargs):
        super(JobAlertForm, self).__init__(*args, **kwargs)
        if str(self.data.get("user_authenticated")) == "True":
            self.fields["email"].required = False

        if self.data.get("min_year") or self.data.get("max_year"):
            self.fields["max_year"].required = True
            self.fields["min_year"].required = True

        if self.data.get("min_salary") or self.data.get("max_salary"):
            self.fields["max_salary"].required = True
            self.fields["min_salary"].required = True

    def clean_name(self):
        name = self.data.get("name", "")
        alerts = JobAlert.objects.filter(name__iexact=name).exclude(id=self.instance.id)
        if alerts.exists():
            raise forms.ValidationError("Alert Already Exists with This Name")
        return name

    def clean_max_salary(self):
        max_salary = self.cleaned_data.get("max_salary")
        if self.cleaned_data.get("min_salary") and max_salary:
            if int(max_salary) < int(self.cleaned_data.get("min_salary")):
                raise forms.ValidationError(
                    "Maximum salary must be greater than minimum salary"
                )
            return max_salary
        return max_salary

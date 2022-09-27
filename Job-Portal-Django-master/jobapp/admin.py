from django.contrib import admin
from .models import Category, News, Applicant, Job, BookmarkJob, JobAlert, Skill, Subscriber, DailySearchLog, SearchResult


admin.site.register(Category)
admin.site.register(News)
admin.site.register(Skill)
admin.site.register(JobAlert)
admin.site.register(Subscriber)
admin.site.register(DailySearchLog)
admin.site.register(SearchResult)

class ApplicantAdmin(admin.ModelAdmin):
    list_display = ('job','user','timestamp')
    
admin.site.register(Applicant,ApplicantAdmin)


class JobAdmin(admin.ModelAdmin):
    list_display = ('title','is_published','is_closed','timestamp')

admin.site.register(Job,JobAdmin)

class BookmarkJobAdmin(admin.ModelAdmin):
    list_display = ('job','user','timestamp')
admin.site.register(BookmarkJob,BookmarkJobAdmin)



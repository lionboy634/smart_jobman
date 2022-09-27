from django.urls import path
from jobapp import views

app_name = "jobapp"


urlpatterns = [

    path('', views.home_view, name='home'),
    path('jobs/', views.job_list_View, name='job-list'),
    path('company/', views.company_view, name='company-list'),
    path('company/review/<int:id>/', views.review, name='review'),
    path('alert/create/', views.job_alert, name='job-alert'),
    path('schedule/meeting/', views.create_meeting , name='meeting'),
    path('alert/results/<int:alert_id>/', views.job_alert_results, name='job-alert-result'),
    path('upload/resume/', views.upload_resume, name='upload_resume' ),
    path('edit/personalinfo/', views.edit_personalinfo , name='edit_personalinfo' ),
    path('jobs/recommended/', views.recommended_jobs),
    path('news/<int:id>/', views.news_list_view, name='single-new'),
    path('job/create/', views.create_job_View, name='create-job'),
    path('job/<int:id>/', views.single_job_view, name='single-job'),
    path('apply-job/<int:id>/', views.apply_job_view, name='apply-job'),
    path('bookmark-job/<int:id>/', views.job_bookmark_view, name='bookmark-job'),
    path('about/', views.single_job_view, name='about'),
    path('contact/', views.single_job_view, name='contact'),
    path('result/', views.search_result_view, name='search_result'),
    path('dashboard/result/', views.recruit_search_view , name='recruit_search'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/employer/job/<int:id>/applicants/', views.all_applicants_view, name='applicants'),
    path('dashboard/employer/job/edit/<int:id>', views.job_edit_view, name='edit-job'),
    path('dashboard/employer/applicant/<int:id>/', views.applicant_details_view, name='applicant-details'),
    path('dashboard/employer/close/<int:id>/', views.make_complete_job_view, name='complete'),
    path('dashboard/employer/delete/<int:id>/', views.delete_job_view, name='delete'),
    path('dashboard/employee/delete-bookmark/<int:id>/', views.delete_bookmark_view, name='delete-bookmark'),


]

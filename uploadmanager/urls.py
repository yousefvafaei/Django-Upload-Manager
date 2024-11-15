from django.urls import path
from . import views

app_name = "uploadmanager"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("file/upload/", views.FileUploadView.as_view(), name="file_upload"),
    # path("file/upload/<slug:parent_slug>/", views.FileUploadView.as_view(), name="file_upload_with_folder"),
    path('file/<int:pk>/update/', views.FileUpdateView.as_view(), name="file_update"),
    path('file/<int:pk>/delete/', views.FileDeleteView.as_view(), name='file_delete'),
    path('file/<int:file_id>/', views.FileDetailView.as_view(), name='file_detail'),
    path('folder/create/', views.FolderCreateView.as_view(), name='folder_create'),
    # path("folder/create/<slug:folder_slug>/", views.FolderCreateView.as_view(), name="folder_create_with_parent"),
    path('folder/<slug:slug>/', views.FolderDetailView.as_view(), name='folder_detail'),
    path('folder/<slug:slug>/update/', views.FolderUpdateView.as_view(), name='folder_update'),
    path('folder/<slug:slug>/delete/', views.FolderDeleteView.as_view(), name='folder_delete'),
    path('search/', views.SearchView.as_view(), name='search'),
]

import logging
import os
import time

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Folder, File
from uploadmanager.forms import FileUploadForm, FileUpdateForm, FolderCreateForm, FolderUpdateForm


class HomeView(LoginRequiredMixin, View):
    template_name = 'uploadmanager/home.html'

    def get(self, request, *args, **kwargs):
        upload_form = FileUploadForm()
        create_folder = FolderCreateForm()

        files = File.objects.filter(user=request.user, folder__isnull=True).order_by('-created_at')
        folders = Folder.objects.filter(user=request.user, is_parent=None).order_by('-created_at')

        is_empty = not files.exists() and not folders.exists()

        context = {
            "files": files,
            "folders": folders,
            "upload_form": upload_form,
            "create_folder": create_folder,
            "is_empty": is_empty,
        }

        return render(request, self.template_name, context)


class FileUploadView(LoginRequiredMixin, View):
    form_class = FileUploadForm
    template_name = 'uploadmanager/home.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'form': self.form_class, })

    def post(self, request, *args, **kwargs):
        folder_slug = request.POST.get('parent_slug', None)
        folder = None
        if folder_slug:
            folder = get_object_or_404(Folder, slug=folder_slug)

        form = self.form_class(request.POST, request.FILES)

        if form.is_valid():
            try:
                new_file = form.save(commit=False)
                if folder:
                    new_file.folder = folder
                new_file.user = request.user
                new_file.save()

                if folder:
                    return HttpResponseRedirect(f'/folder/{folder.slug}/')
                else:
                    return HttpResponseRedirect('/')
            except ValidationError as e:
                form.add_error(None, str(e))
        return render(request, self.template_name, {'upload_form': form})


class FileDetailView(View):
    def get(self, request, *args, **kwargs):
        file_id = kwargs.get('file_id')
        file = get_object_or_404(File, id=file_id)

        return render(request, 'uploadmanager/file-detail.html', {'file': file})


class FileUpdateView(LoginRequiredMixin, View):
    form_class = FileUpdateForm

    def get(self, request, pk):
        file = get_object_or_404(File, pk=pk)
        form = self.form_class(instance=file)
        return render(request, "uploadmanager/file-update.html", {'form_update': form, 'file': file})

    def post(self, request, pk):
        file = get_object_or_404(File, pk=pk)
        form = self.form_class(request.POST, instance=file)

        if form.is_valid():
            new_file = form.save(commit=False)
            if request.user.is_authenticated and request.user == new_file.user:
                new_file.save()
                messages.success(request, 'File updated successfully!', 'success')
                return redirect('uploadmanager:home')
            else:
                messages.error(request, 'You do not have permission to edit this file.', 'danger')

        return render(request, "uploadmanager/file-update.html", {'form_update': form, 'file': file})


class FileDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        file = get_object_or_404(File, pk=pk)

        if request.user.is_authenticated and request.user == file.user:
            folder = file.folder
            file.delete()
            messages.success(request, 'File deleted successfully.', 'success')

            if folder:
                return redirect('uploadmanager:folder_detail', slug=folder.slug)
            else:
                return redirect('uploadmanager:home')
        else:
            messages.error(request, 'You do not have permission to delete this file.', 'danger')
            return redirect('uploadmanager:home')


class FolderCreateView(LoginRequiredMixin, View):
    form_class = FolderCreateForm
    upload_form = FileUploadForm
    template_name = 'uploadmanager/home.html'

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            new_folder = form.save(commit=False)
            new_folder.user = request.user
            parent_slug = request.POST.get("parent_slug")
            if parent_slug:
                try:
                    parent_folder = Folder.objects.get(slug=parent_slug)
                    new_folder.is_parent = parent_folder
                except Folder.DoesNotExist:
                    messages.error(request, "Parent folder does not exist.", "danger")
                except ValidationError as e:
                    form.add_error(None, str(e))
            new_folder.save()
            messages.success(request, 'Your Folder was created successfully!', 'success')

            return redirect('uploadmanager:folder_detail', slug=new_folder.slug)

        folders = Folder.objects.filter(user=request.user)
        return render(request, self.template_name, {'form': form, 'folders': folders, 'upload_form': self.upload_form})


class FolderDetailView(View):
    template_name = 'uploadmanager/home.html'

    def get(self, request, slug, *args, **kwargs):
        folder = get_object_or_404(Folder, slug=slug)
        files = File.objects.filter(folder=folder)
        subfolders = Folder.objects.filter(is_parent=folder)
        upload_form = FileUploadForm()

        context = {
            'folder': folder,
            'files': files,
            'subfolders': subfolders,
            'upload_form': upload_form,
        }

        return render(request, self.template_name, context)


class FolderUpdateView(LoginRequiredMixin, View):
    form_class = FolderUpdateForm

    def get(self, request, slug):
        folder = get_object_or_404(Folder, slug=slug)
        form = self.form_class(instance=folder)
        return render(request, "uploadmanager/folder-update.html", {'form_update': form, 'folder': folder})

    def post(self, request, slug):
        folder = get_object_or_404(Folder, slug=slug)
        form = self.form_class(request.POST, instance=folder)
        if form.is_valid():
            new_folder = form.save(commit=False)
            if request.user.is_authenticated and request.user == new_folder.user:
                new_folder.save()
                messages.success(request, 'Folder updated successfully!', 'success')
                return redirect('uploadmanager:home')
            else:
                messages.error(request, 'You do not have permission to edit this Folder.', 'danger')
        return render(request, "uploadmanager/folder-update.html", {'form_update': form, 'folder': folder})


class FolderDeleteView(LoginRequiredMixin, View):
    def post(self, request, slug):
        folder = get_object_or_404(Folder, slug=slug)

        if request.user.is_authenticated and request.user == folder.user:
            files = File.objects.filter(folder=folder)
            for file in files:
                file.delete()

            try:
                folder.delete()
                messages.success(request, 'Folder deleted successfully.', 'success')
            except Exception as e:
                messages.error(request, f'Error deleting folder: {e}', 'danger')

        return redirect('uploadmanager:home')


class SearchView(View):
    def get(self, request, *args, **kwargs):
        search_query = self.request.GET.get("search", "").strip()

        files = File.objects.filter(
            user=request.user, name__icontains=search_query
        ).order_by("name")

        folders = Folder.objects.filter(
            user=request.user, name__icontains=search_query
        ).order_by("name")

        search_title = f'Search results for: "{search_query}"' if search_query else "Search results"

        no_results = not files.exists() and not folders.exists()
        if no_results:
            messages.info(request, "No results found.", "info")

        context = {
            "search_title": search_title,
            "files": files,
            "folders": folders,
            "no_results": no_results,
        }

        return render(request, "uploadmanager/search-list.html", context)

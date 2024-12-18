from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Folder, File
from uploadmanager.forms import FileUploadForm, FileUpdateForm, FolderCreateForm, FolderUpdateForm


class HomeView(LoginRequiredMixin, View):
    """
    View for displaying the homepage with a list of files and folders for the logged-in user.

    Handles:
        - Displaying the user's files and folders.
        - Providing forms to upload files and create new folders.

    Template:
        'uploadmanager/home.html'

    Context:
        - files: List of files without a parent folder.
        - folders: List of top-level folders.
        - upload_form: Form for uploading files.
        - create_folder: Form for creating new folders.
        - is_empty: Boolean flag indicating if no files or folders exist.
    """
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
    """
    Handles the file upload functionality for users.

    GET request:
        - Displays the upload form and lists the user's files and folders.

    POST request:
        - Handles the file upload, saving the file to the specified folder or root if no folder is selected.

    Attributes:
        form_class: The form used for file uploads (FileUploadForm).
        template_name: The template for rendering the view ('uploadmanager/home.html').

    """
    form_class = FileUploadForm
    template_name = 'uploadmanager/home.html'

    def get(self, request, *args, **kwargs):
        context = {
            'upload_form': self.form_class(),
            'files': File.objects.filter(user=request.user, folder__isnull=True),
            'folders': Folder.objects.filter(user=request.user, is_parent=None),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests. Saves the uploaded file to the specified folder, or to the root folder if no folder is specified.

        Context:
            - 'upload_form': The file upload form with possible validation errors.
            - 'files': List of files in the selected folder or the user's files.
            - 'folders': List of folders in the selected folder or the user's folders.
            - 'folder': The folder the file is being uploaded to.

        Redirects:
            - Redirects to the folder detail page if a folder is specified, or the home page if no folder is specified.
        """
        folder_slug = request.POST.get('parent_slug')
        folder = get_object_or_404(Folder, slug=folder_slug) if folder_slug else None

        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            new_file = form.save(commit=False)
            new_file.folder = folder
            new_file.user = request.user
            new_file.save()
            return HttpResponseRedirect(f'/folder/{folder.slug}/' if folder else '/')

        context = {
            'upload_form': form,
            'files': File.objects.filter(folder=folder) if folder else File.objects.filter(user=request.user,
                                                                                           folder__isnull=True),
            'folders': Folder.objects.filter(is_parent=folder) if folder else Folder.objects.filter(user=request.user,
                                                                                                    is_parent=None),
            'folder': folder,
        }
        return render(request, self.template_name, context)


class FileDetailView(View):
    """
    View for displaying the details of a specific file.

    Handles:
        - GET request: Displays the file's details like name, size, type, etc.

    Template:
        'uploadmanager/file-detail.html'

    Context:
        - file: The file instance to display.
    """

    def get(self, request, *args, **kwargs):
        file_id = kwargs.get('file_id')
        file = get_object_or_404(File, id=file_id)

        return render(request, 'uploadmanager/file-detail.html', {'file': file})


class FileUpdateView(LoginRequiredMixin, View):
    """
    View for updating the details of a file (e.g., name, description, etc.).

    Handles:
        - GET request: Displays the file update form.
        - POST request: Updates the file's details and saves the changes.

    Template:
        'uploadmanager/file-update.html'

    Context:
        - form_update: The form for updating the file's details.
        - file: The file instance being updated.
    """
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

                if file.folder:
                    parent_folder = file.folder
                    return redirect('uploadmanager:folder_detail', slug=parent_folder.slug)
                else:
                    return redirect('uploadmanager:home')
            else:
                messages.error(request, 'You do not have permission to edit this file.', 'danger')

        return render(request, "uploadmanager/file-update.html", {'form_update': form, 'file': file})


class FileDeleteView(LoginRequiredMixin, View):
    """
    View for deleting a file from the system.

    Handles:
        - POST request: Deletes the file and redirects to the appropriate page (folder or homepage).

    Context:
        - success message if the file was deleted.
    """

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
    """
    Handles the creation of new folders for the user.

    POST request:
        - Creates a new folder, optionally within a parent folder, and redirects to the folder detail or home page.

    Attributes:
        form_class: The form used for folder creation (FolderCreateForm).
        template_name: The template for rendering the view ('uploadmanager/home.html').
    """
    form_class = FolderCreateForm
    template_name = 'uploadmanager/home.html'

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests. Creates a new folder and assigns it to the parent folder if specified.

        Context:
            - 'upload_form': The file upload form.
            - 'form': The folder creation form with potential validation errors.
            - 'folder': The parent folder if a subfolder is being created.
            - 'folders': List of top-level folders (if no parent folder is specified).
            - 'subfolders': List of subfolders under the parent folder.
            - 'files': List of files under the parent folder.

        Redirects:
            - Redirects to the folder detail page if a parent folder exists, or to the home page if no parent is selected.
        """
        parent_slug = request.POST.get('parent_slug', None)
        parent_folder = get_object_or_404(Folder, slug=parent_slug) if parent_slug else None

        form = self.form_class(request.POST)

        if form.is_valid():
            new_folder = form.save(commit=False)
            new_folder.user = request.user
            new_folder.is_parent = parent_folder
            new_folder.save()

            messages.success(request, f"Folder '{new_folder.name}' created successfully.")

            return redirect('uploadmanager:folder_detail', slug=parent_slug) if parent_folder else redirect(
                'uploadmanager:home')

        folders = Folder.objects.filter(user=request.user, is_parent=None) if not parent_folder else []
        subfolders = Folder.objects.filter(is_parent=parent_folder) if parent_folder else []
        files = File.objects.filter(folder=parent_folder) if parent_folder else []

        context = {
            'upload_form': FileUploadForm(),
            'form': form,
            'folder': parent_folder,
            'folders': folders,
            'subfolders': subfolders,
            'files': files,
        }

        return render(request, self.template_name, context)


class FolderDetailView(View):
    """
    View for displaying the details of a specific folder.

    Handles:
        - GET request: Displays the folder's contents (files and subfolders).

    Template:
        'uploadmanager/home.html'

    Context:
        - folder: The folder being viewed.
        - files: The list of files inside the folder.
        - subfolders: The list of subfolders inside the folder.
        - upload_form: The file upload form.
    """
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
    """
    View for updating the details of an existing folder.

    Handles:
        - GET request: Displays the folder update form.
        - POST request: Updates the folder's details.

    Template:
        'uploadmanager/folder-update.html'

    Context:
        - form_update: The form for updating the folder's details.
        - folder: The folder instance being updated.
    """
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
                if folder.is_parent:
                    return redirect('uploadmanager:folder_detail', slug=folder.is_parent.slug)
                else:
                    return redirect('uploadmanager:home')
            else:
                messages.error(request, 'You do not have permission to edit this Folder.', 'danger')
        return render(request, "uploadmanager/folder-update.html", {'form_update': form, 'folder': folder})


class FolderDeleteView(LoginRequiredMixin, View):
    """
    View for deleting a folder from the system.

    Handles:
        - POST request: Deletes the folder and its contents, and redirects to the appropriate parent folder or homepage.

    Context:
        - success message if the folder was deleted.
    """

    def post(self, request, slug):
        folder = get_object_or_404(Folder, slug=slug)

        if request.user.is_authenticated and request.user == folder.user:
            parent_folder = folder.is_parent
            folder.delete()
            messages.success(request, 'Folder deleted successfully.', 'success')

            if parent_folder:
                return redirect('uploadmanager:folder_detail', slug=parent_folder.slug)
            else:
                return redirect('uploadmanager:home')
        else:
            messages.error(request, 'You do not have permission to delete this folder.', 'danger')
            return redirect('uploadmanager:home')


class SearchView(View):
    """
    View for searching files and folders based on a query string.
    """

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to search for files and folders.

        Retrieves the query from the request, searches for matching files and folders
        owned by the user, and prepares the context for rendering the results.
        """
        search_query = self.request.GET.get("search", "").strip()

        # Filter files and folders based on the search query and user ownership
        files = File.objects.filter(
            user=request.user, name__icontains=search_query
        ).order_by("name")
        folders = Folder.objects.filter(
            user=request.user, name__icontains=search_query
        ).order_by("name")

        # Build the full path for each folder, including parent folders
        for folder in folders:
            path = self.get_folder_path(folder)
            folder.path = path  # Add the folder path to the search results

        # Build the full path for each file based on its parent folder
        for file in files:
            path = self.get_folder_path(file.folder)  # Handle cases where the file might be in a folder
            file.path = path  # Add the file path to the search results

        # Prepare a title for the search results
        search_title = f'Search results for: "{search_query}"' if search_query else "Search results"

        # Check if no results were found
        no_results = not files.exists() and not folders.exists()

        if no_results:
            messages.info(request, "No results found.", "info")  # Notify the user if nothing matches the search

        # Render the search results page with relevant context
        context = {
            "search_title": search_title,
            "files": files,
            "folders": folders,
            "no_results": no_results,
        }

        return render(request, "uploadmanager/search-list.html", context)

    def get_folder_path(self, folder):
        """
        Recursively get the full path of a folder including all parent folders.

        Args:
            folder (Folder): The folder instance for which the path is to be determined.

        Returns:
            str: A string representing the folder path in the format "Parent / Subfolder / Folder".
                If the folder is None, returns "Home" or another suitable indicator.
        """
        if not folder:
            return "Home"  # Use "Home" or another suitable placeholder for top-level files

        path_parts = [folder.name]
        parent_folder = folder.is_parent

        # Traverse up the hierarchy to build the full path
        while parent_folder:
            if not parent_folder.name:
                break  # Exit the loop if the parent folder is invalid
            path_parts.insert(0, parent_folder.name)  # Add the parent folder's name to the beginning of the path
            parent_folder = parent_folder.is_parent  # Move up to the next parent folder

        return " / ".join(path_parts)  # Combine all parts into a single path string

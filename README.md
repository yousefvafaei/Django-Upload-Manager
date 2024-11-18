# Django Upload Manager

A Dockerized File Management System built with Django that allows authenticated users to upload, manage, and organize files in a structured folder system.

## Features
- User registration and login using email and a secure password.
- Upload image and video files (10MB limit for images, 50MB limit for videos).
- View previously uploaded files with details (name, creation date, update date, size).
- Create and manage folders with nested structures.
- Rename files and folders.
- Delete files and folders with confirmation.
- Thumbnail generation for images and videos.
- Search functionality for files and folders.
- Breadcrumb navigation for folder structures.
- Modal view for displaying detailed information about files and folders.

## Getting Started

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yousefvafaei/Django-Upload-Manager.git
   cd Django-Upload-Manager
   ```

2. Create a `.env` file in the project root and add the required environment variables. Example:
   ```env
   SECRET_KEY=your-secret-key
   DEBUG=True
   DB_NAME=your-database-name
   DB_USER=your-database-user
   DB_PASSWORD=your-database-password
   DB_HOST=db
   DB_PORT=5432
   ```

3. Build and run the project using Docker Compose:
   ```bash
   docker-compose up --build
   ```

4. Apply migrations to set up the database:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

5. Create a superuser for the admin panel:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

### Running the Application
To access the application, open your browser and go to:
```
http://localhost:8000
```

### Project Commands
- To stop the project:
  ```bash
  docker-compose down
  ```
- To rebuild the project after changes:
  ```bash
  docker-compose up --build
  ```

### Notes
- Ensure the `.env` file is created and properly configured before running the project.
- Only image and video files are supported for upload.

## Repository
The project repository is available on GitHub:
[https://github.com/yousefvafaei/Django-Upload-Manager](https://github.com/yousefvafaei/Django-Upload-Manager)

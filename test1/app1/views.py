import firebase_admin
from firebase_admin import credentials, db
import requests
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
import os
from tempfile import NamedTemporaryFile

# Initialize Firebase Admin SDK
if not firebase_admin._apps:  # Avoid reinitialization error
    try:
        # Fetch the service account JSON from an environment variable
        service_account_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')

        if not service_account_json:
            raise ValueError("The 'GOOGLE_APPLICATION_CREDENTIALS_JSON' environment variable is not set.")

        # Write the JSON content to a temporary file
        with NamedTemporaryFile(mode="w", delete=False, suffix=".json") as temp_file:
            temp_file.write(service_account_json)
            temp_file_path = temp_file.name

        try:
            # Use the temporary file for Firebase Admin initialization
            cred = credentials.Certificate(temp_file_path)
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://musify-2ad60-default-rtdb.asia-southeast1.firebasedatabase.app'
            })
        finally:
            # Ensure the temporary file is deleted after initialization
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    except Exception as e:
        raise Exception(f"Error initializing Firebase Admin SDK: {e}")

# Helper function to add a user to Firebase
def add_user_to_firebase(username, name, email):
    try:
        ref = db.reference('users')
        ref.child(username).set({
            'name': name,
            'email': email,
            'username': username,
        })
        return True
    except Exception as e:
        return str(e)

# Register view
def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password == confirm_password:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Email already registered.')
            else:
                firebase_status = add_user_to_firebase(username, name, email)
                if firebase_status is True:
                    try:
                        User.objects.create_user(username=username, first_name=name, email=email, password=password)
                        messages.success(request, 'Registration successful! Please log in.')
                        return redirect('login')
                    except Exception as e:
                        messages.error(request, f'Error creating Django user: {str(e)}')
                else:
                    messages.error(request, f'Error in Firebase: {firebase_status}')
        else:
            messages.error(request, 'Passwords do not match.')

    return render(request, 'register.html')

# Login view
def login_view(request):
    if request.user.is_authenticated:  # Redirect if already logged in
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')

# Logout view
def logout_view(request):
    logout(request)
    messages.add_message(request, messages.INFO, 'You have been logged out.', extra_tags='logout')
    return redirect('login')

# Home view
@login_required
def home(request):
    name = request.user.first_name
    return render(request, 'home.html', {'name': name})

# Track download view
def track_download(request):
    song = request.GET.get('song', '')
    quality = 'hq'

    if not song:
        messages.error(request, "Please provide a valid song name.")
        return redirect('home')

    url = 'https://spotify-scraper.p.rapidapi.com/v1/track/download/soundcloud'
    headers = {
        "x-rapidapi-key": "d1e755b5fdmsh7d3b470e8011a74p14d5bdjsne96a9adf56d5",
        "x-rapidapi-host": "spotify-scraper.p.rapidapi.com"
    }
    params = {'track': song, 'quality': quality}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        context = {
            'soundcloud_track': data.get('soundcloudTrack', {}),
            'spotify_track': data.get('spotifyTrack', {}),
        }
        return render(request, 'search.html', context)

    except requests.exceptions.HTTPError as http_err:
        messages.error(request, f"HTTP error: {http_err}")
    except requests.exceptions.RequestException as req_err:
        messages.error(request, f"Request error: {req_err}")
    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {e}")

    return render(request, 'Error.html')

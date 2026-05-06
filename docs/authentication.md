**Authentication (Signup & Signin)**

This document describes how signup and signin were implemented in the project, where the code lives, and the runtime flow.

**Overview:**
- **Signup flow:** The index view collects an email and redirects to the signup page. The `signup` view creates a Django `User` using the email as the username and password provided by the user.
- **Signin flow:** The `signin` view authenticates with `username=email` and `password`, logs the user in and redirects to the `profiles` page.
- **Session/profile:** After login, users manage or create profiles; the active profile id is stored in `request.session['profile_id']`.

**Where to look (key files):**
- **Views (core):** [core/views.py](core/views.py#L1-L400) — signup, signin, profiles, create_profile, logout.
- **URLs:** [core/urls.py](core/urls.py#L1-L20) — route names: `index`, `signup`, `login`, `logout`, `profiles`, `create_profile`.
- **Templates:** [core/templates/core/signup.html](core/templates/core/signup.html#L1-L200) and [core/templates/core/signin.html](core/templates/core/signin.html#L1-L200).

**Detailed Signup Flow**

- Entry point:
  - User visits the landing page handled by the `index` class-based view ([core/views.py](core/views.py#L1-L40)). The landing page includes a simple email capture form.
  - If an email is entered and it does not already exist, the view redirects to `/signup/?email=<entered-email>`.

- Signup page (`signup` view):
  - File: [core/views.py](core/views.py#L29-L46)
  - Template: [core/templates/core/signup.html](core/templates/core/signup.html#L1-L80)
  - GET: shows the email (from query param) and a password field.
  - POST: validates password non-empty, uses `User.objects.create_user(username=email, email=email, password=password)` to create the user, saves, and adds a success message (`messages.success`). The view then redirects to the login page (named `login`).

- Key implementation notes:
  - The project uses the email as the Django `User.username` (so authentication uses `username=email`).
  - CSRF protection is enabled in the template via `{% csrf_token %}`.
  - Errors are communicated via Django `messages`.

**Relevant code excerpt (signup)**

```python
# core/views.py (signup)
if request.method == "POST":
    password = request.POST.get('password','').strip()
    if not password:
        messages.error(request, "Password is required")
        return redirect(f'/signup/?email={email}')

    user = User.objects.create_user(username=email, email=email, password=password)
    user.save()

    messages.success(request, "Account created successfully. Signin to Explore!")
    return redirect('login')
```

**Detailed Signin Flow**

- Entry point:
  - The signin form is served by the `signin` view and template when a GET request is made.
  - Template: [core/templates/core/signin.html](core/templates/core/signin.html#L1-L120)

- POST handling (`signin` view):
  - File: [core/views.py](core/views.py#L48-L66)
  - The view reads `email` and `password` from `request.POST` and validates both are present.
  - Calls `authenticate(request, username=email, password=password)`.
  - If `authenticate` returns a `User` object, it calls `auth_login(request, user)` and redirects to the `profiles` page.
  - On failure, it sets an error message and redirects back to `login`.

**Relevant code excerpt (signin)**

```python
# core/views.py (signin)
if request.method=="POST":
    email = request.POST.get('email','').strip()
    password = request.POST.get('password','').strip()

    if not email or not password:
        messages.error(request,"Both email and password are required")
        return redirect('login')

    user = authenticate(request, username=email, password=password)

    if user is not None:
        auth_login(request, user)
        return redirect('profiles')
    else:
        messages.error(request,"Invalid email or password")
        return redirect('login')
```

**Logout**
- File: [core/views.py](core/views.py#L170-L178)
- Simple logout view calls `logout(request)` and redirects to `login`.

**Profiles & Session**
- After authentication, users are directed to manage or choose profiles. The app uses `request.session['profile_id']` to track the active profile.
- See `create_profile`, `profiles_view`, and `select_profile` in [core/views.py](core/views.py#L66-L140).

**URL routing**
- Key routes are defined in [core/urls.py](core/urls.py#L1-L20):
  - `path('signup/', views.signup, name='signup')`
  - `path('login/', views.signin, name='login')`
  - `path('logout/', views.logout_view, name='logout')`

**Templates**
- `signup.html` shows the provided email (query param) and a password input; POSTs back to the same URL.
- `signin.html` contains email/password fields and submits via POST to the same `login` route.

**Security & Behavior Notes**
- Passwords are stored via Django's `create_user`, which hashes passwords properly.
- The app treats the email as the username; there is no separate email field verification step.
- No rate-limiting or account-locked behavior is implemented in these views — add if needed.
- Password complexity/strength checks are not enforced here; consider adding validation or using Django's built-in auth forms for production.

**Next steps / Suggestions**
- Add email verification to confirm ownership of the email address.
- Use Django's `AuthenticationForm` and `UserCreationForm` or custom forms to centralize validation.
- Add unit tests for signup/signin flows, including invalid inputs and redirects.

---
File saved: docs/authentication.md

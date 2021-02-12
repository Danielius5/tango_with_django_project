from django.shortcuts import render

from rango.models import Category, Page

from rango.forms import CategoryForm, PageForm
from django.shortcuts import redirect
from django.urls import reverse
from rango.forms import UserForm, UserProfileForm

from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

from datetime import datetime


def index(request):
    
    category_list = Category.objects.order_by('-likes')[:5]
    
    page_list = Page.objects.order_by('-views')[:5]
    
    context_dict = {}
    
    context_dict['boldmessage'] = 'Crunchy, creamy, cookie, candy, cupcake!'
    
    context_dict['categories'] = category_list
    
    context_dict['pages'] = page_list
    
    visitor_cookie_handler(request)
        
    response = render(request, 'rango/index.html', context=context_dict)
    
    return response

def about(request):
    visitor_cookie_handler(request)
    

    if request.session.test_cookie_worked():
        print("TEST COOKIE WORKED!")
        request.session.delete_test_cookie()
        
    return render(request, 'rango/about.html', {'visits' : request.session['visits']})

def show_category(request, category_name_slug):
    
    context_dict = {}
    
    try:
        category = Category.objects.get(slug=category_name_slug)
        
        pages = Page.objects.filter(category=category)
        
        context_dict['pages'] = pages
        
        context_dict['category'] = category
    
    except Category.DoesNotExist:
        context_dict['category'] = None
        context_dict['pages'] = None

    return render(request, 'rango/category.html', context=context_dict)

@login_required
def add_category(request):
    form = CategoryForm()
    # A HTTP POST?
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        
        # Have we been provided with a valid form?
        if form.is_valid():
            # Save the new category to the database.
            form.save(commit=True)
            # Now that the category is saved, we could confirm this.
            # For now, just redirect the user back to the index view.
            return redirect(reverse('rango:index'))
        else:
            # The supplied form contained errors -
            # just print them to the terminal.
            print(form.errors)
            
    # Will handle the bad form, new form, or no form supplied cases.
    # Render the form with error messages (if any).
    return render(request, 'rango/add_category.html', {'form': form})

@login_required
def add_page(request, category_name_slug):
    
    try:
        category = Category.objects.get(slug=category_name_slug)
    
    except Category.DoesNotExist:
        category = None
        
    if category is None:
        return redirect(reverse('rango:index'))
        
    
    form = PageForm()

    if request.method == 'POST':
        
        form = PageForm(request.POST)
        

        if form.is_valid():

            page = form.save(commit=False)
            page.category = category
            page.views = 0
            page.save()

            return redirect(reverse('rango:show_category',
                    kwargs={'category_name_slug':
                    category_name_slug}))
        
        else:

            print(form.errors)
            
    return render(request, 'rango/add_page.html', context={'form' : form, 'category' : category})


def register(request):
    
    # A boolean value for telling the template
    # whether the registration was successful.
    # Set to False initially. Code changes value to
    # True when registration succeeds.
    registered = False
    
    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        
        # If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's form data to the database.
            user = user_form.save()
            
            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.save()
            
            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves,
            # we set commit=False. This delays saving the model
            # until we're ready to avoid integrity problems.
            profile = profile_form.save(commit=False)
            profile.user = user
            
            # Did the user provide a profile picture?
            # If so, we need to get it from the input form and
            #put it in the UserProfile model.
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']
            
            # Now we save the UserProfile model instance.
            profile.save()
            
            # Update our variable to indicate that the template
            # registration was successful.
            registered = True
        else:
            # Invalid form or forms - mistakes or something else?
            # Print problems to the terminal.
            print(user_form.errors, profile_form.errors)
    else:
        # Not a HTTP POST, so we render our form using two ModelForm instances.
        # These forms will be blank, ready for user input.
        user_form = UserForm()
        profile_form = UserProfileForm()
        
    # Render the template depending on the context.
    return render(request,
    'rango/register.html',
    context = {'user_form': user_form,
    'profile_form': profile_form,
    'registered': registered})

def user_login(request):
    
    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        # We use request.POST.get('<variable>') as opposed
        # to request.POST['<variable>'], because the
        # request.POST.get('<variable>') returns None if the
        # value does not exist, while request.POST['<variable>']
        # will raise a KeyError exception.
        
        username = request.POST.get('username')
        
        password = request.POST.get('password')
        
        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        
        user = authenticate(username=username, password=password)
        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        
        if user:
            
            # Is the account active? It could have been disabled.
            if user.is_active:
                
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return redirect(reverse('rango:index'))
            else:
                
                # An inactive account was used - no logging in!
                return HttpResponse("Your Rango account is disabled.")
        else:
            
            # Bad login details were provided. So we can't log the user in.
            print(f"Invalid login details: {username}, {password}")
            return HttpResponse("Invalid login details supplied.")
        # The request is not a HTTP POST, so display the login form.
        # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render(request, 'rango/login.html')


@login_required
def restricted(request):
    return render(request, 'rango/restricted.html')


@login_required
def user_logout(request):
    
    # Since we know the user is logged in, we can now just log them out.
    logout(request)
    
    # Take the user back to the homepage.
    return redirect(reverse('rango:index'))


# A helper method
def get_server_side_cookie(request, cookie, default_val=None):
    val = request.session.get(cookie)
    if not val:
        val = default_val
    return val

# Updated the function definition
def visitor_cookie_handler(request):
    
    visits = int(get_server_side_cookie(request, 'visits', '1'))
    last_visit_cookie = get_server_side_cookie(request,
                        'last_visit',
                        str(datetime.now()))
    
    last_visit_time = datetime.strptime(last_visit_cookie[:-7],
                                        '%Y-%m-%d %H:%M:%S')
        
    # If it's been more than a day since the last visit...
    if (datetime.now() - last_visit_time).days > 0:
        visits = visits + 1
        # Update the last visit cookie now that we have updated the count
        request.session['last_visit'] = str(datetime.now())
    else:
        # Set the last visit cookie
        request.session['last_visit'] = last_visit_cookie
    # Update/set the visits cookie
    request.session['visits'] = visits


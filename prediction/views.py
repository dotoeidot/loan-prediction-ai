
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView


# Homepage - Only accessible to authenticated users
@login_required
def home(request):
    return render(request, 'home.html')


# Login
class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = False

    def get_success_url(self):
        return '/'


# Registration
def register(request):

    if request.method == 'POST':

        form = UserCreationForm(request.POST)

        if form.is_valid():

            user = form.save(commit=False)

            user.first_name = request.POST.get('full_name', '').strip()
            user.email = request.POST.get('email', '').strip()

            user.save()

            # Redirect to login after successful registration
            return redirect('login')

    else:
        form = UserCreationForm()

    return render(request, 'register.html', {'form': form})

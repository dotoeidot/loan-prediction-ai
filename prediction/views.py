
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView

from .ml_model import predict_loan_uptake


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

            return redirect('login')

    else:
        form = UserCreationForm()

    return render(request, 'register.html', {'form': form})


# Loan Prediction
@login_required
def loan_prediction(request):

    result = None
    error = None

    if request.method == 'POST':

        try:
            input_data = [
                int(request.POST.get('age')),
                int(request.POST.get('experience')),
                float(request.POST.get('income')),
                int(request.POST.get('family')),
                float(request.POST.get('ccavg')),
                int(request.POST.get('education')),
                float(request.POST.get('mortgage')),
                int(request.POST.get('securities_account')),
                int(request.POST.get('cd_account')),
                int(request.POST.get('online')),
                int(request.POST.get('credit_card'))
            ]

            result = predict_loan_uptake(input_data)

        except (ValueError, TypeError):
            error = "Please enter valid values for all fields."

    if result:
        return render(request, 'loan_prediction_result.html', {
        'result': result
    })

    return render(request, 'loan_prediction.html', {
    'error': error
})

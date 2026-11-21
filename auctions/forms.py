from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import Auction

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ('username','email','password1','password2')

class AuctionForm(forms.ModelForm):
    duration_minutes = forms.IntegerField(min_value=1, max_value=10080, initial=15, help_text='1 minute to 7 days')
    class Meta:
        model = Auction
        fields = ['title','description','category','image_url','starting_price','minimum_increment']
        widgets = {'description':forms.Textarea(attrs={'rows':4})}
    def save(self, commit=True, seller=None):
        obj = super().save(commit=False)
        obj.seller = seller
        obj.current_price = obj.starting_price
        obj.ends_at = timezone.now() + timedelta(minutes=self.cleaned_data['duration_minutes'])
        if commit: obj.save()
        return obj

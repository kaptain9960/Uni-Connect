from django import forms
from .models import Thread, Reply, Course


class ThreadForm(forms.ModelForm):
    attachment = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control glass-input'}))
    voice_note = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control glass-input'}))

    class Meta:
        model = Thread
        fields = ['course', 'title', 'content', 'tags', 'attachment', 'voice_note']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control glass-input', 'placeholder': 'Ask a clear, specific question...'}),
            'content': forms.Textarea(attrs={'class': 'form-control glass-input', 'rows': 6, 'placeholder': 'Provide context, what you have tried, relevant course material...'}),
            'tags': forms.CheckboxSelectMultiple(attrs={'class': 'tag-checkbox'}),
            'course': forms.Select(attrs={'class': 'form-select glass-input'}),
        }

    def __init__(self, *args, **kwargs):
        department = kwargs.pop('department', None)
        super().__init__(*args, **kwargs)
        if department:
            self.fields['course'].queryset = Course.objects.filter(department=department, is_active=True)


class ReplyForm(forms.ModelForm):
    attachment = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control glass-input'}))
    voice_note = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control glass-input'}))

    class Meta:
        model = Reply
        fields = ['content', 'attachment', 'voice_note']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control glass-input',
                'rows': 4,
                'placeholder': 'Share your knowledge, be clear and helpful...'
            }),
        }


class ChatMessageForm(forms.Form):
    content = forms.CharField(required=False, widget=forms.Textarea(attrs={
        'class': 'form-control glass-input',
        'rows': 3,
        'placeholder': 'Type a message or attach a file...'
    }))
    attachment = forms.FileField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control glass-input'}))


class SearchForm(forms.Form):
    q = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control glass-input',
            'placeholder': 'Search threads, courses, topics...',
        })
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.filter(is_active=True),
        required=False,
        empty_label='All Courses',
        widget=forms.Select(attrs={'class': 'form-select glass-input'})
    )
    status = forms.ChoiceField(
        choices=[('', 'Any Status'), ('open', 'Open'), ('resolved', 'Resolved')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select glass-input'})
    )

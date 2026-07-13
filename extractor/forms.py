from django import forms

class UploadForm(forms.Form):

    file = forms.FileField()

class ChatForm(forms.Form):

    question = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder":"Ask anything"
            }
        )
    )
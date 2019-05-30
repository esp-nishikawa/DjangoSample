from django import forms
from django.contrib.auth import forms as auth_forms
from .models import User, Category, Item


class AuthenticationForm(auth_forms.AuthenticationForm):
    """
    ログインフォーム
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label


class UserCreationForm(auth_forms.UserCreationForm):
    """
    ユーザー登録フォーム
    """
    class Meta:
        model = User
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        # メールアドレスが仮登録段階の場合は削除
        email = self.cleaned_data['email']
        User.objects.filter(email=email, is_active=False).delete()
        return email


class EmailChangeForm(forms.ModelForm):
    """
    メールアドレス変更フォーム
    """
    class Meta:
        model = User
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label

    def clean_email(self):
        # メールアドレスが仮登録段階の場合は削除
        email = self.cleaned_data['email']
        User.objects.filter(email=email, is_active=False).delete()
        return email


class PasswordChangeForm(auth_forms.PasswordChangeForm):
    """
    パスワード変更フォーム
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class PasswordResetForm(auth_forms.PasswordResetForm):
    """
    パスワード再設定用メール送信フォーム
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label


class SetPasswordForm(auth_forms.SetPasswordForm):
    """
    パスワード再設定フォーム
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class CategoryForm(forms.ModelForm):
    """
    カテゴリフォーム
    """
    class Meta:
        model = Category
        fields = ('name',)
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
            }),
        }


class ItemForm(forms.ModelForm):
    """
    アイテムフォーム
    """
    class Meta:
        model = Item
        fields = ('title','description','image','url','mark',)
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control-file',
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
            }),
            'mark': forms.Select(attrs={
                'class': 'form-control',
            }),
        }

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core import signing
from django.core.mail import send_mail
from django.http import HttpResponseNotFound
from django.shortcuts import redirect
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.views import generic
from . import forms

User = get_user_model()

class Top(LoginRequiredMixin, generic.TemplateView):
    """
    トップページ
    """
    template_name = 'top.html'

class Done(generic.TemplateView):
    """
    完了ページ
    """
    template_name = 'done.html'

class Login(auth_views.LoginView):
    """
    ログインページ
    """
    form_class = forms.LoginForm
    template_name = 'login.html'

class UserCreation(generic.CreateView):
    """
    ユーザー登録ページ
    """
    form_class = forms.UserCreationForm
    template_name = 'user_creation.html'

    def form_valid(self, form):
        # 仮登録
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        # 本登録用メールの送付
        current_site = get_current_site(self.request)
        domain = current_site.domain
        context = {
            'protocol': 'https' if self.request.is_secure() else 'http',
            'domain': domain,
            'token': signing.dumps(user.pk),
        }
        subject_template = get_template('email/user_creation_subject.txt')
        subject = subject_template.render(context)
        message_template = get_template('email/user_creation_message.txt')
        message = message_template.render(context)
        user.email_user(subject, message)

        # 完了ページにリダイレクト
        messages.success(self.request, 'ユーザー登録用メールを送信しました。現時点ではユーザー登録は完了していません。\nメールが届きましたら、本文中に記載されているURLからユーザー登録を行ってください。')
        return redirect('webapp:done')

class UserCreationComplete(generic.TemplateView):
    """
    ユーザー登録完了ページ
    """
    template_name = 'done.html'
    timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)

    def get(self, request, **kwargs):
        # tokenを確認して問題なければ本登録
        token = kwargs.get('token')
        try:
            user_pk = signing.loads(token, max_age=self.timeout_seconds)

        # 期限切れ
        except signing.SignatureExpired:
            messages.error(self.request, 'ユーザー登録用URLの有効期限がきれました。お手数をお掛けしますが、再度ユーザー登録を行って下さい。')
            return super().get(request, **kwargs)

        # tokenが間違い
        except signing.BadSignature:
            return HttpResponseNotFound()

        # 問題なし
        else:
            try:
                user = User.objects.get(pk=user_pk)
            except User.DoesNotExist:
                return HttpResponseNotFound()
            else:
                if not user.is_active:
                    # 本登録
                    user.is_active = True
                    user.save()
                messages.success(self.request, 'ユーザー登録が完了しました。\n登録されたメールアドレスとパスワードでログインしてください。')
                return super().get(request, **kwargs)

class UserDetail(LoginRequiredMixin, UserPassesTestMixin, generic.DetailView):
    """
    ユーザー情報ページ
    """
    model = User
    template_name = 'user_detail.html'

    def test_func(self):
        # 本人 or スーパーユーザーのみアクセスを許可する
        user = self.request.user
        return user.pk == self.kwargs['pk'] or user.is_superuser

class EmailChange(LoginRequiredMixin, generic.FormView):
    """
    メールアドレス変更ページ
    """
    form_class = forms.EmailChangeForm
    template_name = 'email_change.html'

    def get_initial(self):
        initial = super().get_initial()
        initial['email'] = self.request.user.email
        return initial

    def form_valid(self, form):
        user = self.request.user
        new_email = form.cleaned_data['email']

        # メールアドレス変更用メールの送付
        current_site = get_current_site(self.request)
        domain = current_site.domain
        context = {
            'protocol': 'https' if self.request.is_secure() else 'http',
            'domain': domain,
            'token1': signing.dumps(user.pk),
            'token2': signing.dumps(new_email),
        }
        subject_template = get_template('email/email_change_subject.txt')
        subject = subject_template.render(context)
        message_template = get_template('email/email_change_message.txt')
        message = message_template.render(context)
        send_mail(subject, message, None, [new_email])

        # 完了ページにリダイレクト
        messages.success(self.request, 'メールアドレス変更用メールを送信しました。\nメールが届きましたら、本文中に記載されているURLからメールアドレスの変更を行ってください。')
        return redirect('webapp:done')

class EmailChangeComplete(LoginRequiredMixin, generic.TemplateView):
    """
    メールアドレス変更完了ページ
    """
    template_name = 'done.html'
    timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)

    def get(self, request, **kwargs):
        # tokenを確認して問題なければメールアドレス変更
        token1 = kwargs.get('token1')
        token2 = kwargs.get('token2')
        try:
            user_pk = signing.loads(token1, max_age=self.timeout_seconds)
            new_email = signing.loads(token2, max_age=self.timeout_seconds)

        # 期限切れ
        except signing.SignatureExpired:
            messages.error(self.request, 'メールアドレス変更用URLの有効期限がきれました。お手数をお掛けしますが、再度メールアドレスの変更を行って下さい。')
            return super().get(request, **kwargs)

        # tokenが間違い
        except signing.BadSignature:
            return HttpResponseNotFound()

        # 問題なし
        else:
            if request.user.pk == user_pk:
                # メールアドレス変更
                User.objects.filter(email=new_email, is_active=False).delete()
                request.user.email = new_email
                request.user.save()
                messages.success(self.request, 'メールアドレスの変更が完了しました。')
                return super().get(request, **kwargs)
            else:
                return HttpResponseNotFound()

class PasswordChange(auth_views.PasswordChangeView):
    """
    パスワード変更ページ
    """
    form_class = forms.PasswordChangeForm
    template_name = 'password_change.html'
    success_url = reverse_lazy('webapp:done')

    def form_valid(self, form):
        messages.success(self.request, 'パスワードを変更しました。')
        return super().form_valid(form)

class PasswordReset(auth_views.PasswordResetView):
    """
    パスワード再設定用メール送信ページ
    """
    form_class = forms.PasswordResetForm
    template_name = 'password_reset.html'
    subject_template_name = 'email/password_reset_subject.txt'
    email_template_name = 'email/password_reset_message.txt'
    success_url = reverse_lazy('webapp:done')

    def form_valid(self, form):
        messages.success(self.request, 'パスワード再設定用メールを送信しました。\nメールが届きましたら、本文中に記載されているURLからパスワードの再設定を行ってください。')
        return super().form_valid(form)

class PasswordResetConfirm(auth_views.PasswordResetConfirmView):
    """
    パスワード再設定ページ
    """
    form_class = forms.SetPasswordForm
    template_name = 'password_reset_confirm.html'
    success_url = reverse_lazy('webapp:done')

    def form_valid(self, form):
        messages.success(self.request, 'パスワードを再設定しました。\n登録されたメールアドレスとパスワードでログインしてください。')
        return super().form_valid(form)

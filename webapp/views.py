from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.sites.shortcuts import get_current_site
from django.core import signing
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q, Count
from django.http import HttpResponseNotFound
from django.shortcuts import redirect
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.views import generic
from . import forms
from .models import User, Category, Item


class Top(LoginRequiredMixin, generic.TemplateView):
    """
    トップページ
    """
    template_name = 'top.html'

    def render_to_response(self, context):
        # カテゴリ一覧 or アイテム一覧ページにリダイレクト
        category_count = Category.objects.filter(owner=self.request.user).count()
        if category_count > 0:
            return redirect('webapp:category_list')
        else:
            return redirect('webapp:item_list')
        return super().render_to_response(context)


class Login(auth_views.LoginView):
    """
    ログインページ
    """
    form_class = forms.AuthenticationForm
    template_name = 'login.html'


class UserCreate(generic.CreateView):
    """
    ユーザー登録ページ
    """
    form_class = forms.UserCreationForm
    template_name = 'user_create.html'

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
        subject_template = get_template('email/user_create_subject.txt')
        subject = subject_template.render(context)
        message_template = get_template('email/user_create_message.txt')
        message = message_template.render(context)
        user.email_user(subject, message)

        # 完了ページにリダイレクト
        messages.success(self.request, 'ユーザー登録用メールを送信しました。現時点ではユーザー登録は完了していません。\nメールが届きましたら、本文中に記載されているURLからユーザー登録を行ってください。')
        return redirect('webapp:done')


class UserCreateComplete(generic.TemplateView):
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


class UserDelete(LoginRequiredMixin, UserPassesTestMixin, generic.DeleteView):
    """
    ユーザー削除ページ
    """
    model = User
    template_name = 'user_delete.html'
    success_url = reverse_lazy('webapp:done')

    def delete(self, request, *args, **kwargs):
        result = super().delete(request, *args, **kwargs)
        messages.success(self.request, 'ユーザーを削除しました。')
        return result

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


class Done(generic.TemplateView):
    """
    完了ページ
    """
    template_name = 'done.html'


class CategoryList(LoginRequiredMixin, generic.ListView):
    """
    カテゴリ一覧ページ
    """
    model = Category
    context_object_name = 'category_list'
    template_name = 'category_list.html'
    paginate_by = 10

    def get_queryset(self):
        # オーナーで絞り込み＆アイテム数を設定
        return super().get_queryset().filter(
            owner=self.request.user
        ).annotate(
            item_count=Count('item', filter=Q(item__owner=self.request.user))
        ).order_by('order', '-created_at')

    def get_context_data(self, **kwargs):
        # リストの最初と最後のカテゴリを設定
        context = super().get_context_data(**kwargs)
        if len(self.object_list) > 0:
            context['first_pk'] = self.object_list.first().pk
            context['last_pk'] = self.object_list.last().pk

        # カテゴリなしのアイテム数を設定
        null_item_count = Item.objects.filter(owner=self.request.user).filter(category__isnull=True).count()
        context['null_item_count'] = null_item_count
        return context

    @transaction.atomic
    def post(self, request, **kwargs):
        self.object_list = self.get_queryset()
        if 'up' in request.POST:
            # 上に移動
            current_pk = request.POST.get('up')
            current = self.object_list.get(pk=current_pk)
            prev = self.object_list.filter(order__lt=current.order).last()
            prev_order = prev.order
            prev.order = current.order
            current.order = prev_order
            current.save()
            prev.save()

        elif 'down' in request.POST:
            # 下に移動
            current_pk = request.POST.get('down')
            current = self.object_list.get(pk=current_pk)
            next = self.object_list.filter(order__gt=current.order).first()
            next_order = next.order
            next.order = current.order
            current.order = next_order
            current.save()
            next.save()

        # リストを再表示
        return redirect('webapp:category_list')


class CategoryCreate(LoginRequiredMixin, generic.CreateView):
    """
    カテゴリ追加ページ
    """
    model = Category
    form_class = forms.CategoryForm
    template_name = 'category_create.html'
    success_url = reverse_lazy('webapp:top')

    def form_valid(self, form):
        # その他のカテゴリの順序を+1する
        categorys = []
        for category in Category.objects.filter(owner=self.request.user):
            category.order = category.order + 1
            categorys.append(category)
        Category.objects.bulk_update(categorys, fields=['order'])

        # オーナーを設定
        form.instance.owner = self.request.user
        messages.success(self.request, 'カテゴリ（{}）を追加しました。'.format(form.instance.name))
        return super().form_valid(form)


class CategoryUpdate(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    """
    カテゴリ変更ページ
    """
    model = Category
    form_class = forms.CategoryForm
    template_name = 'category_update.html'
    success_url = reverse_lazy('webapp:top')

    def form_valid(self, form):
        messages.success(self.request, 'カテゴリ（{}）を変更しました。'.format(form.instance.name))
        return super().form_valid(form)

    def test_func(self):
        # オーナー or スーパーユーザーのみアクセスを許可する
        user = self.request.user
        category = self.get_object()
        return user == category.owner or user.is_superuser


class CategoryDelete(LoginRequiredMixin, UserPassesTestMixin, generic.DeleteView):
    """
    カテゴリ削除ページ
    """
    model = Category
    template_name = 'category_delete.html'
    success_url = reverse_lazy('webapp:top')

    def delete(self, request, *args, **kwargs):
        result = super().delete(request, *args, **kwargs)
        messages.success(self.request, 'カテゴリ（{}）を削除しました。'.format(self.object.name))
        return result

    def get_context_data(self, **kwargs):
        # カテゴリ内のアイテムリストを設定
        context = super().get_context_data(**kwargs)
        category = self.get_object()
        item_list = Item.objects.filter(owner=self.request.user).filter(category=category).order_by('order', '-created_at')
        context['item_list'] = item_list
        return context

    def test_func(self):
        # オーナー or スーパーユーザーのみアクセスを許可する
        user = self.request.user
        category = self.get_object()
        return user == category.owner or user.is_superuser


class ItemList(LoginRequiredMixin, generic.ListView):
    """
    アイテム一覧ページ
    """
    model = Item
    context_object_name = 'item_list'
    template_name = 'item_list.html'
    paginate_by = 10

    def get_queryset(self):
        # オーナー＆カテゴリで絞り込み
        queryset = super().get_queryset().filter(owner=self.request.user)
        category_pk = self.request.GET.get('category')
        if category_pk is None:
            queryset = queryset.filter(category__isnull=True)
        else:
            queryset = queryset.filter(category=category_pk)
        return queryset.order_by('order', '-created_at')

    def get_context_data(self, **kwargs):
        # カテゴリ数＆カテゴリ情報を設定
        context = super().get_context_data(**kwargs)
        category_list = Category.objects.filter(owner=self.request.user)
        category_count = len(category_list)
        context['category_count'] = category_count
        if category_count > 0:
            category_pk = self.request.GET.get('category')
            if category_pk is not None:
                context['category'] = category_list.get(pk=category_pk)

        # リストの最初と最後のアイテムを設定
        if len(self.object_list) > 0:
            context['first_pk'] = self.object_list.first().pk
            context['last_pk'] = self.object_list.last().pk
        return context

    @transaction.atomic
    def post(self, request, **kwargs):
        self.object_list = self.get_queryset()
        if 'up' in request.POST:
            # 上に移動
            current_pk = request.POST.get('up')
            current = self.object_list.get(pk=current_pk)
            prev = self.object_list.filter(order__lt=current.order).last()
            prev_order = prev.order
            prev.order = current.order
            current.order = prev_order
            current.save()
            prev.save()

        elif 'down' in request.POST:
            # 下に移動
            current_pk = request.POST.get('down')
            current = self.object_list.get(pk=current_pk)
            next = self.object_list.filter(order__gt=current.order).first()
            next_order = next.order
            next.order = current.order
            current.order = next_order
            current.save()
            next.save()

        # リストを再表示
        response = redirect('webapp:item_list')
        category_pk = request.GET.get('category')
        if category_pk is not None:
            response['location'] += '?category={}'.format(category_pk)
        return response


class ItemCreate(LoginRequiredMixin, generic.CreateView):
    """
    アイテム追加ページ
    """
    model = Item
    form_class = forms.ItemForm
    template_name = 'item_create.html'

    def get_form_kwargs(self):
        # フォームにユーザー＆カテゴリを渡す
        kwargs = super().get_form_kwargs()
        kwargs.update({ 'user': self.request.user })
        kwargs.update({ 'category': self.request.GET.get('category') })
        return kwargs

    def form_valid(self, form):
        # その他のアイテムの順序を+1する
        items = []
        for item in Item.objects.filter(owner=self.request.user):
            item.order = item.order + 1
            items.append(item)
        Item.objects.bulk_update(items, fields=['order'])

        # オーナーを設定
        form.instance.owner = self.request.user
        messages.success(self.request, 'アイテム（{}）を追加しました。'.format(form.instance.title))
        return super().form_valid(form)

    def get_success_url(self):
        success_url = reverse_lazy('webapp:item_list')
        category_pk = self.request.GET.get('category')
        if category_pk is not None:
            success_url += '?category={}'.format(category_pk)
        return success_url


class ItemUpdate(LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView):
    """
    アイテム変更ページ
    """
    model = Item
    form_class = forms.ItemForm
    template_name = 'item_update.html'

    def get_form_kwargs(self):
        # フォームにユーザー＆カテゴリを渡す
        kwargs = super().get_form_kwargs()
        kwargs.update({ 'user': self.request.user })
        kwargs.update({ 'category': self.request.GET.get('category') })
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'アイテム（{}）を変更しました。'.format(form.instance.title))
        return super().form_valid(form)

    def get_success_url(self):
        success_url = reverse_lazy('webapp:item_list')
        category_pk = self.request.GET.get('category')
        if category_pk is not None:
            success_url += '?category={}'.format(category_pk)
        return success_url

    def test_func(self):
        # オーナー or スーパーユーザーのみアクセスを許可する
        user = self.request.user
        item = self.get_object()
        return user == item.owner or user.is_superuser


class ItemDelete(LoginRequiredMixin, UserPassesTestMixin, generic.DeleteView):
    """
    アイテム削除ページ
    """
    model = Item
    template_name = 'item_delete.html'

    def delete(self, request, *args, **kwargs):
        result = super().delete(request, *args, **kwargs)
        messages.success(self.request, 'アイテム（{}）を削除しました。'.format(self.object.title))
        return result

    def get_success_url(self):
        success_url = reverse_lazy('webapp:item_list')
        category_pk = self.request.GET.get('category')
        if category_pk is not None:
            success_url += '?category={}'.format(category_pk)
        return success_url

    def test_func(self):
        # オーナー or スーパーユーザーのみアクセスを許可する
        user = self.request.user
        item = self.get_object()
        return user == item.owner or user.is_superuser

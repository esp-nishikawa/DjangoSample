from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _


class UserManager(BaseUserManager):
    """
    ユーザーマネージャー
    """
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given email, and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    カスタムユーザーモデル
    """
    username = models.CharField(_('username'), max_length=150, blank=True)
    email = models.EmailField(_('email address'), unique=True)

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []


class Category(models.Model):
    """
    カテゴリモデル
    """
    name = models.CharField(
        verbose_name='名前',
        max_length=100,
    )
    order = models.IntegerField(
        verbose_name='順序',
        default=0,
    )
    owner = models.ForeignKey(
        User,
        verbose_name='オーナー',
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(
        verbose_name='作成日時',
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        verbose_name='更新日時',
        auto_now=True,
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'カテゴリ'
        verbose_name_plural = 'カテゴリ'


class Item(models.Model):
    """
    アイテムモデル
    """
    MARK_CHOICES = (
        (1, '〇'),
        (2, '△'),
        (3, '×'),
    )

    title = models.CharField(
        verbose_name='タイトル',
        max_length=100,
    )
    description = models.TextField(
        verbose_name='説明',
        max_length=2000,
        blank=True,
        null=True,
    )
    image = models.ImageField(
        verbose_name='画像',
        upload_to='images/',
        null=True,
        blank=True,
    )
    url = models.URLField(
        verbose_name='URL',
        blank=True,
        null=True,
    )
    mark = models.IntegerField(
        verbose_name='マーク',
        choices=MARK_CHOICES,
        blank=True,
        null=True,
    )
    category = models.ForeignKey(
        Category,
        verbose_name='カテゴリ',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    order = models.IntegerField(
        verbose_name='順序',
        default=0,
    )
    owner = models.ForeignKey(
        User,
        verbose_name='オーナー',
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(
        verbose_name='作成日時',
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        verbose_name='更新日時',
        auto_now=True,
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'アイテム'
        verbose_name_plural = 'アイテム'

@receiver(models.signals.pre_save, sender=Item)
def item_pre_save(sender, instance, **kwargs):
    # アイテムの保存時に古い画像ファイルを削除
    if instance.pk:
        try:
            item = Item.objects.get(pk=instance.pk)
            if item.image:
                if item.image != instance.image:
                    item.image.delete(False)
        except Item.DoesNotExist:
            pass

@receiver(models.signals.post_delete, sender=Item)
def item_post_delete(sender, instance, **kwargs):
    # アイテムの削除時に画像ファイルを削除
    if instance.image:
        instance.image.delete(False)

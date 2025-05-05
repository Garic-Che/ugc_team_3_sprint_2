import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


class MyUserManager(BaseUserManager):
    def create_user(self, login, password=None):
        if not login:
            raise ValueError("Users must have a login")
        if not password:
            raise ValueError("User must have a password")

        user = self.model(login=login)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, login, password=None):
        if not password:
            raise ValueError("Superuser must have a password")
        user = self.create_user(login, password=password)
        user.is_staff = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    login = models.CharField(verbose_name="login", max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # строка с именем поля модели,
    # которая используется в качестве уникального идентификатора
    USERNAME_FIELD = "login"

    # менеджер модели
    objects = MyUserManager()

    def __str__(self):
        return f"{self.login} {self.id}"

    class Meta:
        db_table = 'content"."user'
        ordering = ("login",)

    def has_perm(self, perm, obj=None):
        if self.is_staff:
            return True
        return False

    def has_module_perms(self, app_label):
        if self.is_staff:
            return True
        return False

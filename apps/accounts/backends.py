from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Backend d'authentification permettant la connexion par email OU username.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            return None

        # Chercher par email d'abord (insensible à la casse)
        try:
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            # Sinon chercher par username
            try:
                user = User.objects.get(username__iexact=username)
            except User.DoesNotExist:
                # Exécuter le hash pour éviter les attaques par timing
                User().set_password(password)
                return None
            except User.MultipleObjectsReturned:
                return None
        except User.MultipleObjectsReturned:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
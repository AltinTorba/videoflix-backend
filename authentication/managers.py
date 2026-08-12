from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """Manager for the email-based custom user model."""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user.

        Args:
            email: Email address (required, used for login).
            password: Plain-text password, stored hashed.
            **extra_fields: Additional fields on the user model.

        Returns:
            User: The newly created user object.

        Raises:
            ValueError: If no email address was provided.
        """
        if not email:
            raise ValueError("The email address is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create an active superuser with staff and admin rights.

        Args:
            email: Email address of the superuser.
            password: Plain-text password.
            **extra_fields: Additional fields on the user model.

        Returns:
            User: The newly created superuser object.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)

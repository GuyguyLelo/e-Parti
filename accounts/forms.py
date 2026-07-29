"""Formulaires comptes — authentification et gestion des utilisateurs."""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from accounts.models import User
from territoires.models import Province, SectionLocale


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Identifiant",
        widget=forms.TextInput(attrs={"class": "form-control", "autofocus": True}),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )


class UserCreateForm(UserCreationForm):
    """Création d'un utilisateur staff (rôle + périmètre)."""

    class Meta:
        model = User
        fields = [
            "username",
            "nom",
            "post_nom",
            "prenom",
            "email",
            "telephone",
            "role",
            "province",
            "section_locale",
            "is_active",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "post_nom": forms.TextInput(attrs={"class": "form-control"}),
            "prenom": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
            "role": forms.Select(attrs={"class": "form-select"}),
            "province": forms.Select(attrs={"class": "form-select"}),
            "section_locale": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, request_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request_user = request_user
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password2"].widget.attrs.update({"class": "form-control"})
        self.fields["province"].queryset = Province.objects.filter(actif=True).order_by("nom")
        self.fields["section_locale"].queryset = SectionLocale.objects.filter(
            actif=True
        ).select_related("commune__ville__province").order_by("nom")
        self.fields["province"].required = False
        self.fields["section_locale"].required = False
        self.fields["is_active"].initial = True

        # Un provincial ne peut créer que des locaux dans sa province
        if request_user and request_user.is_provincial and not request_user.is_admin_national:
            self.fields["role"].choices = [(User.Role.LOCAL, "Responsable local")]
            self.fields["role"].initial = User.Role.LOCAL
            if request_user.province_id:
                self.fields["province"].queryset = Province.objects.filter(
                    pk=request_user.province_id
                )
                self.fields["province"].initial = request_user.province_id
                self.fields["section_locale"].queryset = self.fields[
                    "section_locale"
                ].queryset.filter(commune__ville__province_id=request_user.province_id)

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get("role")
        province = cleaned.get("province")
        section = cleaned.get("section_locale")

        if role == User.Role.PROVINCIAL and not province:
            self.add_error("province", "Une province est requise pour un responsable provincial.")
        if role == User.Role.LOCAL and not section:
            self.add_error(
                "section_locale", "Une section locale est requise pour un responsable local."
            )
        if role == User.Role.ADMIN_NATIONAL:
            cleaned["province"] = None
            cleaned["section_locale"] = None
        elif role == User.Role.PROVINCIAL:
            cleaned["section_locale"] = None
        elif role == User.Role.LOCAL and section and not province:
            cleaned["province"] = section.province

        if self.request_user and self.request_user.is_provincial and not self.request_user.is_admin_national:
            if role != User.Role.LOCAL:
                self.add_error("role", "Vous ne pouvez créer que des responsables locaux.")
            if section and self.request_user.province_id:
                if section.province != self.request_user.province:
                    self.add_error(
                        "section_locale",
                        "La section doit appartenir à votre province.",
                    )
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    """Modification d'un utilisateur (sans changement de mot de passe obligatoire)."""

    new_password = forms.CharField(
        label="Nouveau mot de passe",
        required=False,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Laisser vide pour ne pas changer"}
        ),
        help_text="Laisser vide pour conserver le mot de passe actuel.",
    )

    class Meta:
        model = User
        fields = [
            "username",
            "nom",
            "post_nom",
            "prenom",
            "email",
            "telephone",
            "role",
            "province",
            "section_locale",
            "is_active",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "post_nom": forms.TextInput(attrs={"class": "form-control"}),
            "prenom": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
            "role": forms.Select(attrs={"class": "form-select"}),
            "province": forms.Select(attrs={"class": "form-select"}),
            "section_locale": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, request_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request_user = request_user
        self.fields["province"].queryset = Province.objects.filter(actif=True).order_by("nom")
        self.fields["section_locale"].queryset = SectionLocale.objects.filter(
            actif=True
        ).select_related("commune__ville__province").order_by("nom")
        self.fields["province"].required = False
        self.fields["section_locale"].required = False

        if request_user and request_user.is_provincial and not request_user.is_admin_national:
            self.fields["role"].choices = [(User.Role.LOCAL, "Responsable local")]
            if request_user.province_id:
                self.fields["province"].queryset = Province.objects.filter(
                    pk=request_user.province_id
                )
                self.fields["section_locale"].queryset = self.fields[
                    "section_locale"
                ].queryset.filter(commune__ville__province_id=request_user.province_id)

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get("role")
        province = cleaned.get("province")
        section = cleaned.get("section_locale")

        if role == User.Role.PROVINCIAL and not province:
            self.add_error("province", "Une province est requise pour un responsable provincial.")
        if role == User.Role.LOCAL and not section:
            self.add_error(
                "section_locale", "Une section locale est requise pour un responsable local."
            )
        if role == User.Role.ADMIN_NATIONAL:
            cleaned["province"] = None
            cleaned["section_locale"] = None
        elif role == User.Role.PROVINCIAL:
            cleaned["section_locale"] = None
        elif role == User.Role.LOCAL and section and not province:
            cleaned["province"] = section.province

        if self.request_user and self.request_user.is_provincial and not self.request_user.is_admin_national:
            if role != User.Role.LOCAL:
                self.add_error("role", "Vous ne pouvez gérer que des responsables locaux.")
            if self.instance.is_admin_national or self.instance.is_provincial:
                raise forms.ValidationError("Vous ne pouvez pas modifier cet utilisateur.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get("new_password")
        if new_password:
            user.set_password(new_password)
        if commit:
            user.save()
        return user

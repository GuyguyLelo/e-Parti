"""Formulaires e-Parti — adhésion et authentification."""
from django import forms
from django.contrib.auth.forms import AuthenticationForm

from membership.models import Adhesion
from territoires.models import Commune, SectionLocale, Ville


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Identifiant",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Nom d'utilisateur"}),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Mot de passe"}),
    )


class AdhesionForm(forms.ModelForm):
    """Formulaire public multi-sections d'adhésion."""

    class Meta:
        model = Adhesion
        fields = [
            "nom",
            "post_nom",
            "prenom",
            "date_naissance",
            "lieu_naissance",
            "sexe",
            "etat_civil",
            "adresse",
            "telephone",
            "email",
            "nationalite",
            "province_origine",
            "type_piece_identite",
            "numero_piece_identite",
            "niveau_etudes",
            "profession",
            "deja_membre",
            "details_membre",
            "motivations",
            "certifie_exactitude",
            "date_signature",
            "photo1",
            "photo2",
            "section_locale",
            "latitude",
            "longitude",
        ]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "post_nom": forms.TextInput(attrs={"class": "form-control"}),
            "prenom": forms.TextInput(attrs={"class": "form-control"}),
            "date_naissance": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"
            ),
            "lieu_naissance": forms.TextInput(attrs={"class": "form-control"}),
            "sexe": forms.Select(attrs={"class": "form-select"}),
            "etat_civil": forms.Select(attrs={"class": "form-select"}),
            "adresse": forms.TextInput(attrs={"class": "form-control"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "nationalite": forms.TextInput(attrs={"class": "form-control"}),
            "province_origine": forms.Select(attrs={"class": "form-select"}),
            "type_piece_identite": forms.Select(attrs={"class": "form-select"}),
            "numero_piece_identite": forms.TextInput(attrs={"class": "form-control"}),
            "niveau_etudes": forms.Select(attrs={"class": "form-select"}),
            "profession": forms.TextInput(attrs={"class": "form-control"}),
            "deja_membre": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "details_membre": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "motivations": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "certifie_exactitude": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "date_signature": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"
            ),
            "photo1": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "photo2": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "section_locale": forms.Select(attrs={"class": "form-select"}),
            "latitude": forms.HiddenInput(),
            "longitude": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["section_locale"].queryset = SectionLocale.objects.filter(
            actif=True
        ).select_related("commune__ville__province")
        self.fields["certifie_exactitude"].required = True

    def clean_certifie_exactitude(self):
        value = self.cleaned_data.get("certifie_exactitude")
        if not value:
            raise forms.ValidationError(
                "Vous devez certifier l'exactitude des informations."
            )
        return value

    def clean_telephone(self):
        tel = self.cleaned_data["telephone"].strip()
        if len(tel) < 9:
            raise forms.ValidationError("Numéro de téléphone invalide.")
        return tel


class MembreUpdateForm(forms.ModelForm):
    """Modification des données d'un membre (fiche adhésion liée)."""

    actif = forms.BooleanField(
        label="Membre actif",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    notes = forms.CharField(
        label="Notes internes",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )

    class Meta:
        model = Adhesion
        fields = [
            "nom",
            "post_nom",
            "prenom",
            "date_naissance",
            "lieu_naissance",
            "sexe",
            "etat_civil",
            "adresse",
            "telephone",
            "email",
            "nationalite",
            "province_origine",
            "type_piece_identite",
            "numero_piece_identite",
            "niveau_etudes",
            "profession",
            "deja_membre",
            "details_membre",
            "motivations",
            "photo1",
            "photo2",
            "section_locale",
        ]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "post_nom": forms.TextInput(attrs={"class": "form-control"}),
            "prenom": forms.TextInput(attrs={"class": "form-control"}),
            "date_naissance": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"
            ),
            "lieu_naissance": forms.TextInput(attrs={"class": "form-control"}),
            "sexe": forms.Select(attrs={"class": "form-select"}),
            "etat_civil": forms.Select(attrs={"class": "form-select"}),
            "adresse": forms.TextInput(attrs={"class": "form-control"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "nationalite": forms.TextInput(attrs={"class": "form-control"}),
            "province_origine": forms.Select(attrs={"class": "form-select"}),
            "type_piece_identite": forms.Select(attrs={"class": "form-select"}),
            "numero_piece_identite": forms.TextInput(attrs={"class": "form-control"}),
            "niveau_etudes": forms.Select(attrs={"class": "form-select"}),
            "profession": forms.TextInput(attrs={"class": "form-control"}),
            "deja_membre": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "details_membre": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "motivations": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "photo1": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "photo2": forms.ClearableFileInput(attrs={"class": "form-control", "accept": "image/*"}),
            "section_locale": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, membre=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.membre = membre
        self.fields["section_locale"].queryset = SectionLocale.objects.filter(
            actif=True
        ).select_related("commune__ville__province")
        self.fields["date_naissance"].input_formats = ["%Y-%m-%d"]
        if membre is not None:
            self.fields["actif"].initial = membre.actif
            self.fields["notes"].initial = membre.notes

    def clean_telephone(self):
        tel = self.cleaned_data["telephone"].strip()
        if len(tel) < 9:
            raise forms.ValidationError("Numéro de téléphone invalide.")
        return tel

    def save(self, commit=True):
        adhesion = super().save(commit=commit)
        if self.membre is not None and commit:
            self.membre.actif = self.cleaned_data.get("actif", False)
            self.membre.notes = self.cleaned_data.get("notes", "")
            self.membre.save(update_fields=["actif", "notes"])
        return adhesion


class RejetAdhesionForm(forms.Form):
    motif = forms.CharField(
        label="Motif du rejet",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        required=True,
    )


class CotisationForm(forms.ModelForm):
    class Meta:
        from finances.models import Cotisation

        model = Cotisation
        fields = [
            "membre",
            "montant",
            "devise",
            "date_paiement",
            "type",
            "reference",
            "mode_paiement",
            "notes",
        ]
        widgets = {
            "membre": forms.Select(attrs={"class": "form-select"}),
            "montant": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "devise": forms.TextInput(attrs={"class": "form-control"}),
            "date_paiement": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"
            ),
            "type": forms.Select(attrs={"class": "form-select"}),
            "reference": forms.TextInput(attrs={"class": "form-control"}),
            "mode_paiement": forms.TextInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class EvenementForm(forms.ModelForm):
    class Meta:
        from organisation.models import Evenement

        model = Evenement
        fields = [
            "titre",
            "description",
            "type",
            "date",
            "lieu",
            "province",
            "section_locale",
            "participants_attendus",
        ]
        widgets = {
            "titre": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "type": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "lieu": forms.TextInput(attrs={"class": "form-control"}),
            "province": forms.Select(attrs={"class": "form-select"}),
            "section_locale": forms.Select(attrs={"class": "form-select"}),
            "participants_attendus": forms.NumberInput(attrs={"class": "form-control"}),
        }

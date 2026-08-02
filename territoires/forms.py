"""Formulaires des tables référentielles territoriales."""
from django import forms

from territoires.models import Commune, Province, SectionLocale, Ville


class ProvinceForm(forms.ModelForm):
    class Meta:
        model = Province
        fields = ["nom", "code", "actif"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: KIN"}),
            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class VilleForm(forms.ModelForm):
    class Meta:
        model = Ville
        fields = ["province", "nom", "actif"]
        widgets = {
            "province": forms.Select(attrs={"class": "form-select"}),
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["province"].queryset = Province.objects.filter(actif=True).order_by("nom")


class CommuneForm(forms.ModelForm):
    class Meta:
        model = Commune
        fields = ["ville", "nom", "actif"]
        widgets = {
            "ville": forms.Select(attrs={"class": "form-select"}),
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ville"].queryset = Ville.objects.filter(actif=True).select_related(
            "province"
        ).order_by("province__nom", "nom")


class SectionLocaleForm(forms.ModelForm):
    class Meta:
        model = SectionLocale
        fields = [
            "commune",
            "nom",
            "code",
            "adresse",
            "telephone",
            "actif",
            "latitude",
            "longitude",
        ]
        widgets = {
            "commune": forms.Select(attrs={"class": "form-select"}),
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "adresse": forms.TextInput(attrs={"class": "form-control"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
            "actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "latitude": forms.NumberInput(attrs={"class": "form-control", "step": "0.000001"}),
            "longitude": forms.NumberInput(attrs={"class": "form-control", "step": "0.000001"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commune"].queryset = Commune.objects.filter(actif=True).select_related(
            "ville__province"
        ).order_by("ville__province__nom", "ville__nom", "nom")

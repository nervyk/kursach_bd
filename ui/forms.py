from django import forms
from core.models import (
    Tovar, Postavka, Vyruchka,
    Magazin, Postavshchik, Rabotnik,
    GruppaTovarov, EdinitsaIzmereniya, Bank, Otdel, Dolzhnost
)
from core.models import TovarVyruchka
from core.models import Zayavka, ZayavkaItem
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from core.models import Magazin, Otdel
from django.forms import BaseInlineFormSet
from core.models import Strana, Gorod, Ulitsa

class StranaForm(forms.ModelForm):
    class Meta:
        model = Strana
        fields = ["nazvanie"]

class GorodForm(forms.ModelForm):
    class Meta:
        model = Gorod
        fields = ["nazvanie"]

class UlitsaForm(forms.ModelForm):
    class Meta:
        model = Ulitsa
        fields = ["nazvanie"]


class BaseZayavkaItemFormSet(BaseInlineFormSet):
    """Проверяет, что один и тот же товар не добавлен в заявку дважды."""

    def clean(self):
        super().clean()
        seen = set()
        for form in self.forms:
            if not getattr(form, "cleaned_data", None):
                continue
            if form.cleaned_data.get("DELETE"):
                continue
            tovar = form.cleaned_data.get("id_tovar")
            if not tovar:
                continue
            tid = tovar.pk
            if tid in seen:
                raise forms.ValidationError(
                    "Один и тот же товар указан в заявке несколько раз. Объедините строки."
                )
            seen.add(tid)

def _user_magazin_id(user):
    """
    Возвращает:
      - None: владелец сети / superuser (нет ограничения по магазину)
      - 0: пользователю магазин не назначен
      - int: конкретный id магазина
    """
    if not user or user.is_anonymous:
        return 0
    if user.is_superuser or user.groups.filter(name="Владелец сети").exists():
        return None
    prof = getattr(user, "profile", None)
    mid = getattr(prof, "id_magazin_id", None)
    return mid or 0

class UserCreateForm(UserCreationForm):
    id_magazin = forms.ModelChoiceField(queryset=Magazin.objects.all(), required=False)
    id_otdel = forms.ModelChoiceField(queryset=Otdel.objects.all(), required=False)
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "is_active", "groups")

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            user.groups.set(self.cleaned_data.get("groups"))
            prof = getattr(user, "profile", None)
            if prof:
                prof.id_magazin = self.cleaned_data.get("id_magazin")
                prof.id_otdel = self.cleaned_data.get("id_otdel")
                prof.save()
        return user


class UserUpdateForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "is_active", "groups")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["groups"].initial = self.instance.groups.all()

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            user.groups.set(self.cleaned_data.get("groups"))
        return user
class ZayavkaForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        mid = _user_magazin_id(user)
        can_approve = bool(user and (user.is_superuser or user.has_perm("core.approve_zayavka")))

        if mid:
            self.fields["id_magazin"].queryset = Magazin.objects.filter(pk=mid)
            self.fields["id_magazin"].initial = mid
            self.fields["id_magazin"].disabled = True

        # при редактировании заявки магазин менять нельзя всегда
        if self.instance and self.instance.pk:
            self.fields["id_magazin"].disabled = True

        # обычным пользователям нельзя выставлять APPROVED/REJECTED руками
        if not can_approve:
            self.fields["status"].choices = [
                (Zayavka.Status.DRAFT, "Черновик"),
                (Zayavka.Status.SENT, "Отправлена"),
            ]

    class Meta:
        model = Zayavka
        fields = ["id_magazin", "data_zayavki", "status", "comment"]
        widgets = {"data_zayavki": forms.DateInput(attrs={"type": "date"})}


class ZayavkaItemForm(forms.ModelForm):
    class Meta:
        model = ZayavkaItem
        fields = ["id_tovar", "kolichestvo"]

    def clean_kolichestvo(self):
        v = self.cleaned_data.get("kolichestvo")
        if v is None or v <= 0:
            raise forms.ValidationError("Количество должно быть > 0")
        return v

class TovarForm(forms.ModelForm):
    class Meta:
        model = Tovar
        fields = [
            "nazvanie", "id_edinitsa_izmereniya", "id_gruppa_tovarov",
            "kolichestvo_na_sklade", "cena_postavki", "cena_prodazhi",
        ]

class PostavkaForm(forms.ModelForm):
    class Meta:
        model = Postavka
        fields = ["id_postavshchik", "id_tovar", "data_postavki", "kolichestvo"]
        widgets = {"data_postavki": forms.DateInput(attrs={"type": "date"})}

    def clean_kolichestvo(self):
        v = self.cleaned_data.get("kolichestvo")
        if v is None or v <= 0:
            raise forms.ValidationError("Количество должно быть > 0")
        return v

class VyruchkaForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        mid = _user_magazin_id(user)
        if mid:
            self.fields["id_magazin"].queryset = Magazin.objects.filter(pk=mid)
            self.fields["id_magazin"].initial = mid
            self.fields["id_magazin"].disabled = True

            # работники только этого магазина (через отдел)
            self.fields["id_rabotnik"].queryset = Rabotnik.objects.filter(
                id_otdela__id_magazin_id=mid
            )

        # при редактировании выручки магазин менять нельзя всегда
        if self.instance and self.instance.pk:
            self.fields["id_magazin"].disabled = True

    class Meta:
        model = Vyruchka
        fields = ["data", "id_magazin", "id_rabotnik"]
        widgets = {"data": forms.DateInput(attrs={"type": "date"})}

    def clean(self):
        cleaned = super().clean()
        # подстраховка: если поле disabled, Django не всегда кладёт значение
        if not cleaned.get("id_magazin"):
            # тут value уже ограничено queryset-ом
            cleaned["id_magazin"] = self.fields["id_magazin"].queryset.first()
        return cleaned


class TovarVyruchkaForm(forms.ModelForm):
    class Meta:
        model = TovarVyruchka
        fields = ["id_tovar", "kolichestvo"]

    def clean_kolichestvo(self):
        v = self.cleaned_data.get("kolichestvo")
        if v is None or v <= 0:
            raise forms.ValidationError("Количество должно быть > 0")
        return v

class MagazinForm(forms.ModelForm):
    class Meta:
        model = Magazin
        fields = ["nazvanie", "familiya_direktora", "imya_direktora", "otchestvo_direktora",
                  "id_strana", "id_gorod", "id_ulica"]

class PostavshchikForm(forms.ModelForm):
    class Meta:
        model = Postavshchik
        fields = [
            "nazvanie", "abreviatura", "kod_po_ok",
            "nomer_raschetnogo_scheta", "nomer_telefona",
            "familiya_rukovoditelya", "imya_rukovoditelya", "otchestvo_rukovoditelya",
            "nomer_doma",
            "id_bank", "id_strana", "id_gorod", "id_ulica",
        ]

class RabotnikForm(forms.ModelForm):
    class Meta:
        model = Rabotnik
        fields = [
            "familiya", "imya", "otchestvo", "pol",
            "data_rozhdeniya", "trudovoy_stazh",
            "id_dolzhnost", "id_otdela",
            "nomer_doma", "id_strana", "id_gorod", "id_ulica",
        ]
        widgets = {"data_rozhdeniya": forms.DateInput(attrs={"type": "date"})}

class GruppaTovarovForm(forms.ModelForm):
    class Meta:
        model = GruppaTovarov
        fields = ["nazvanie"]

class EdinitsaIzmereniyaForm(forms.ModelForm):
    class Meta:
        model = EdinitsaIzmereniya
        fields = ["nazvanie"]

class BankForm(forms.ModelForm):
    class Meta:
        model = Bank
        fields = ["nazvanie", "inn", "bik", "nomer_korrespondentnogo_scheta"]

class OtdelForm(forms.ModelForm):
    class Meta:
        model = Otdel
        fields = ["id_magazin", "nazvanie", "id_gruppa_tovarov"]

class DolzhnostForm(forms.ModelForm):
    class Meta:
        model = Dolzhnost
        fields = ["nazvanie"]


# stdlib
import csv
import io
import re
from datetime import date, timedelta
from decimal import Decimal

# django
from django.contrib import messages
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.contrib.auth.models import User
from django.db import connection, transaction
from django.db.models import (
    Count,
    DecimalField,
    ExpressionWrapper,
    F,
    Prefetch,
    Q,
    Sum,
)



from django.db.models.functions import Coalesce
from django.forms import inlineformset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

# local apps
from core.models import (
    Bank,
    Dolzhnost,
    EdinitsaIzmereniya,
    GruppaTovarov,
    Magazin,
    MagazinTovar,
    Otdel,
    Postavka,
    Postavshchik,
    Rabotnik,
    Tovar,
    TovarVyruchka,
    Vyruchka,
    Zayavka,
    ZayavkaItem,
    Strana, 
    Gorod, 
    Ulitsa,
    Professiya, 
    Specialnost, 
    Klassifikaciya, 
    StruktPodrazdelenie,
    MestoRaboty, 
    ZapisiTrudKnizhke,

)
from core.services import (
    StockError,
    ZayavkaApproveError,
    apply_vyruchka_stock,
    approve_zayavka,
)
from .forms import (
    BankForm,
    BaseZayavkaItemFormSet,
    DolzhnostForm,
    EdinitsaIzmereniyaForm,
    GruppaTovarovForm,
    MagazinForm,
    OtdelForm,
    PostavkaForm,
    PostavshchikForm,
    RabotnikForm,
    TovarForm,
    TovarVyruchkaForm,
    UserCreateForm,
    UserUpdateForm,
    VyruchkaForm,
    ZayavkaForm,
    ZayavkaItemForm,
    StranaForm, 
    GorodForm, 
    UlitsaForm,
    ProfessiyaForm, 
    SpecialnostForm, 
    KlassifikaciyaForm, 
    StruktPodrazdelenieForm,
    MestoRabotyForm, 
    ZapisiTrudKnizhkeForm,


)
from .mixins import (
    OwnerOnlyMixin,
    ScopeByMagazinMixin,
    SortSearchListMixin,
)



ZayavkaItemsFormSet = inlineformset_factory(
    Zayavka, ZayavkaItem,
    form=ZayavkaItemForm,
    formset=BaseZayavkaItemFormSet,
    extra=1,
    can_delete=True
)


def _qty_map_from_formset(formset):
    """
    Собирает {tovar_id: total_qty} из валидного formset'а.
    Учитывает DELETE и суммирует повторы одного товара.
    """
    result = {}
    for f in formset.forms:
        if not getattr(f, "cleaned_data", None):
            continue
        if f.cleaned_data.get("DELETE"):
            continue
        tovar = f.cleaned_data.get("id_tovar")
        qty = f.cleaned_data.get("kolichestvo") or 0
        if not tovar or qty <= 0:
            continue
        tid = int(tovar.id)
        result[tid] = result.get(tid, 0) + int(qty)
    return result


class ZayavkaListView(LoginRequiredMixin, PermissionRequiredMixin, ScopeByMagazinMixin, SortSearchListMixin, ListView):
    permission_required = "core.view_zayavka"
    model = Zayavka
    template_name = "ui/zayavka_list.html"
    paginate_by = 20
    allowed_sort = ("id", "data_zayavki", "status")

    def apply_search(self, qs, q: str):
        return qs.filter(
            Q(id_magazin__nazvanie__icontains=q) |
            Q(status__icontains=q)
        )

    def get_queryset(self):
        qs = super().get_queryset()
        return self.scope_qs(qs, "id_magazin")

class ZayavkaCreateView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "core.add_zayavka"
    template_name = "ui/zayavka_form.html"

    def get(self, request, *args, **kwargs):
        form = ZayavkaForm(user=request.user)
        formset = ZayavkaItemsFormSet()
        return self.render_to_response({"form": form, "formset": formset, "title": "Создать заявку"})

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = ZayavkaForm(request.POST, user=request.user)
        formset = ZayavkaItemsFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            z = form.save(commit=False)
            z.created_by = request.user
            z.save()

            items = formset.save(commit=False)
            for it in items:
                it.id_zayavka = z
                it.save()
            for obj in formset.deleted_objects:
                obj.delete()

            return redirect("zayavka_list")

        return self.render_to_response({"form": form, "formset": formset, "title": "Создать заявку"})

class ZayavkaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, ScopeByMagazinMixin, TemplateView):
    permission_required = "core.change_zayavka"
    template_name = "ui/zayavka_form.html"

    def get_object(self):
        qs = self.scope_qs(Zayavka.objects.all(), "id_magazin")
        return get_object_or_404(qs, pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        z = self.get_object()
        form = ZayavkaForm(instance=z, user=request.user)
        formset = ZayavkaItemsFormSet(instance=z)
        return self.render_to_response({"form": form, "formset": formset, "title": "Редактировать заявку", "obj": z})

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        z = self.get_object()
        form = ZayavkaForm(request.POST, instance=z, user=request.user)
        formset = ZayavkaItemsFormSet(request.POST, instance=z)

        if form.is_valid() and formset.is_valid():
            form.save()
            items = formset.save(commit=False)
            for it in items:
                it.save()
            for obj in formset.deleted_objects:
                obj.delete()
            return redirect("zayavka_list")

        return self.render_to_response({"form": form, "formset": formset, "title": "Редактировать заявку", "obj": z})

class ZayavkaApproveView(LoginRequiredMixin, PermissionRequiredMixin, ScopeByMagazinMixin, View):
    permission_required = "core.approve_zayavka"

    def post(self, request, pk: int):
        qs = self.scope_qs(Zayavka.objects.all(), "id_magazin")
        z = get_object_or_404(qs, pk=pk)

        try:
            approve_zayavka(z)
            messages.success(request, f"Заявка #{pk} проведена")
        except ZayavkaApproveError as e:
            messages.error(request, str(e))
        return redirect("zayavka_list")


class ZayavkaSendView(LoginRequiredMixin, PermissionRequiredMixin, ScopeByMagazinMixin, View):
    permission_required = "core.change_zayavka"

    def post(self, request, pk: int):

        qs = self.scope_qs(Zayavka.objects.all(), "id_magazin")


        z = get_object_or_404(qs, pk=pk)


        if z.status != Zayavka.Status.DRAFT:
            messages.warning(request, f"Заявка #{pk} уже отправлена или обработана.")
            return redirect("zayavka_list")

        z.status = Zayavka.Status.SENT
        z.save(update_fields=["status"])
        messages.success(request, f"Заявка #{pk} отправлена.")
        return redirect("zayavka_list")


class ZayavkaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, ScopeByMagazinMixin, DeleteView):
    permission_required = "core.delete_zayavka"
    model = Zayavka
    template_name = "ui/confirm_delete.html"
    success_url = reverse_lazy("zayavka_list")

    def get_queryset(self):
        qs = super().get_queryset()
        return self.scope_qs(qs, "id_magazin")

class MagazinTovarListView(LoginRequiredMixin, PermissionRequiredMixin, ScopeByMagazinMixin, SortSearchListMixin, ListView):
    permission_required = "core.view_magazintovar"
    model = MagazinTovar
    template_name = "ui/magazintovar_list.html"
    paginate_by = 30
    allowed_sort = ("id", "id_tovar__nazvanie", "kolichestvo")

    def apply_search(self, qs, q: str):
        return qs.filter(Q(id_tovar__nazvanie__icontains=q) | Q(id_magazin__nazvanie__icontains=q))

    def get_queryset(self):
        qs = super().get_queryset().select_related("id_magazin", "id_tovar")
        qs = self.scope_qs(qs, "id_magazin")
        return qs

class SpravochnikHomeView(LoginRequiredMixin, TemplateView):
    template_name = "ui/spravochnik_home.html"


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "ui/home.html"

class UserGuideView(LoginRequiredMixin, TemplateView):
    template_name = "ui/help_user_guide.html"


class AboutView(LoginRequiredMixin, TemplateView):
    template_name = "ui/help_about.html"


class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = "ui/settings.html"

    FONT_SCALES = {
        "0.90": "Уменьшенный",
        "1.00": "Обычный",
        "1.15": "Крупный",
        "1.30": "Очень крупный",
    }

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        current = str(self.request.session.get("font_scale", "1.00"))
        if current not in self.FONT_SCALES:
            current = "1.00"
        ctx.update({"font_scales": self.FONT_SCALES, "current_scale": current})
        return ctx

    def post(self, request, *args, **kwargs):
        scale = (request.POST.get("font_scale") or "").strip()
        if scale in self.FONT_SCALES:
            request.session["font_scale"] = scale
            messages.success(request, f"Шрифт: {self.FONT_SCALES[scale]}")
        else:
            messages.error(request, "Некорректное значение настройки")
        return redirect("settings")




# ===== Товары =====
class TovarListView(LoginRequiredMixin, PermissionRequiredMixin, SortSearchListMixin, ListView):
    permission_required = "core.view_tovar"
    model = Tovar
    template_name = "ui/tovar_list.html"
    paginate_by = 20
    allowed_sort = ("id", "nazvanie", "kolichestvo_na_sklade", "cena_postavki", "cena_prodazhi")

    def apply_search(self, qs, q: str):
        return qs.filter(
            Q(nazvanie__icontains=q)
            | Q(id_gruppa_tovarov__nazvanie__icontains=q)
            | Q(id_edinitsa_izmereniya__nazvanie__icontains=q)
        )

class TovarCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "core.add_tovar"
    model = Tovar
    form_class = TovarForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("tovar_list")

class TovarUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "core.change_tovar"
    model = Tovar
    form_class = TovarForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("tovar_list")

class TovarDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "core.delete_tovar"
    model = Tovar
    template_name = "ui/confirm_delete.html"
    success_url = reverse_lazy("tovar_list")


# ===== Поставки =====
class PostavkaListView(LoginRequiredMixin, PermissionRequiredMixin, SortSearchListMixin, ListView):
    permission_required = "core.view_postavka"
    model = Postavka
    template_name = "ui/postavka_list.html"
    paginate_by = 20
    allowed_sort = ("id", "data_postavki", "kolichestvo")

    def apply_search(self, qs, q: str):
        return qs.filter(
            Q(id_postavshchik__nazvanie__icontains=q)
            | Q(id_tovar__nazvanie__icontains=q)
        )

class PostavkaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "core.add_postavka"
    model = Postavka
    form_class = PostavkaForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("postavka_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Добавить поставку"
        return ctx
class PostavkaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "core.change_postavka"
    model = Postavka
    form_class = PostavkaForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("postavka_list")

class PostavkaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "core.delete_postavka"
    model = Postavka
    template_name = "ui/confirm_delete.html"
    success_url = reverse_lazy("postavka_list")


# ===== Выручка =====
class VyruchkaListView(LoginRequiredMixin, PermissionRequiredMixin, ScopeByMagazinMixin, SortSearchListMixin, ListView):
    permission_required = "core.view_vyruchka"
    model = Vyruchka
    template_name = "ui/vyruchka_list.html"
    paginate_by = 20
    allowed_sort = ("id", "data", "qty", "amount")

    def apply_search(self, qs, q: str):
        return qs.filter(
            Q(id_magazin__nazvanie__icontains=q)
            | Q(id_rabotnik__familiya__icontains=q)
            | Q(id_rabotnik__imya__icontains=q)
            | Q(id_rabotnik__otchestvo__icontains=q)
        )

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("id_magazin", "id_rabotnik")
            .prefetch_related(
                Prefetch(
                    "tovarvyruchka_set",
                    queryset=TovarVyruchka.objects.select_related("id_tovar").order_by("id"),
                )
            )
            .annotate(
                qty=Coalesce(Sum("tovarvyruchka__kolichestvo"), 0),
                amount=Coalesce(Sum("tovarvyruchka__summa"), Decimal("0")),
                items_cnt=Coalesce(Count("tovarvyruchka", distinct=True), 0),
            )
        )


        qs = self.scope_qs(qs, "id_magazin")

        q = self.get_search_q()
        if q:
            qs = self.apply_search(qs, q)

        sort, direction = self.get_sort()
        order = f"-{sort}" if direction == "desc" else sort
        return qs.order_by(order)


class VyruchkaCreateView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "core.add_vyruchka"
    template_name = "ui/vyruchka_form.html"

    def get(self, request, *args, **kwargs):
        # На GET форма должна быть НЕ привязана к данным.
        form = VyruchkaForm(user=request.user)
        formset = VyruchkaItemsFormSet()
        return self.render_to_response({"form": form, "formset": formset, "title": "Добавить выручку"})

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = VyruchkaForm(request.POST, user=request.user)
        formset = VyruchkaItemsFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            vyr = form.save(commit=False)
            vyr.save()
            new_map = _qty_map_from_formset(formset)
            try:
                apply_vyruchka_stock(vyr.id_magazin_id, new_map)
            except StockError as e:
                transaction.set_rollback(True)
                messages.error(request, str(e))
                return self.render_to_response({"form": form, "formset": formset, "title": "Добавить выручку"})
            
            items = formset.save(commit=False)
            for it in items:
                if it.cena_prodazhi is None:
                    it.cena_prodazhi = it.id_tovar.cena_prodazhi or Decimal("0")
                qty = it.kolichestvo or 0
                it.summa = (it.cena_prodazhi or Decimal("0")) * Decimal(qty)
                it.id_vyruchka = vyr
                it.save()

            for obj in formset.deleted_objects:
                obj.delete()

            return redirect("vyruchka_list")

        return self.render_to_response({"form": form, "formset": formset, "title": "Добавить выручку"})

VyruchkaItemsFormSet = inlineformset_factory(
    Vyruchka, TovarVyruchka,
    form=TovarVyruchkaForm,
    extra=1,
    can_delete=True
)
class VyruchkaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, ScopeByMagazinMixin, TemplateView):
    permission_required = "core.change_vyruchka"
    template_name = "ui/vyruchka_form.html"

    def get_object(self):
        qs = self.scope_qs(Vyruchka.objects.all(), "id_magazin")
        return get_object_or_404(qs, pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        vyr = self.get_object()
        form = VyruchkaForm(instance=vyr, user=request.user)
        formset = VyruchkaItemsFormSet(instance=vyr)
        return self.render_to_response({"form": form, "formset": formset, "title": "Редактировать выручку"})

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        vyr = self.get_object()
        form = VyruchkaForm(request.POST, instance=vyr, user=request.user)
        formset = VyruchkaItemsFormSet(request.POST, instance=vyr)

        if form.is_valid() and formset.is_valid():
            old_map = {}
            for it in TovarVyruchka.objects.filter(id_vyruchka=vyr).only("id_tovar_id", "kolichestvo"):
                tid = int(it.id_tovar_id)
                old_map[tid] = old_map.get(tid, 0) + int(it.kolichestvo or 0)

            new_map = _qty_map_from_formset(formset)


            delta = {}
            for tid in set(old_map) | set(new_map):
                delta[tid] = old_map.get(tid, 0) - new_map.get(tid, 0)

            try:
                apply_vyruchka_stock(vyr.id_magazin_id, delta)
            except StockError as e:
                transaction.set_rollback(True)
                messages.error(request, str(e))
                return self.render_to_response({"form": form, "formset": formset, "title": "Редактировать выручку"})

            vyr = form.save()

            items = formset.save(commit=False)
            for it in items:
                if it.cena_prodazhi is None:
                    it.cena_prodazhi = it.id_tovar.cena_prodazhi or Decimal("0")
                qty = it.kolichestvo or 0
                it.summa = (it.cena_prodazhi or Decimal("0")) * Decimal(qty)
                it.save()

            for obj in formset.deleted_objects:
                obj.delete()

            return redirect("vyruchka_list")

        return self.render_to_response({"form": form, "formset": formset, "title": "Редактировать выручку"})


class VyruchkaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, ScopeByMagazinMixin, DeleteView):
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        obj = self.get_object()

        # вернуть товары на склад магазина
        back = {}
        for it in TovarVyruchka.objects.filter(id_vyruchka=obj).only("id_tovar_id", "kolichestvo"):
            tid = int(it.id_tovar_id)
            back[tid] = back.get(tid, 0) - int(it.kolichestvo or 0) 

        try:
            apply_vyruchka_stock(obj.id_magazin_id, back)
        except StockError as e:
            transaction.set_rollback(True)
            messages.error(request, str(e))
            return redirect("vyruchka_list")

        return super().delete(request, *args, **kwargs)
    permission_required = "core.delete_vyruchka"
    model = Vyruchka
    template_name = "ui/confirm_delete.html"
    success_url = reverse_lazy("vyruchka_list")

    def get_queryset(self):
        qs = super().get_queryset()
        return self.scope_qs(qs, "id_magazin")


def col(field, label, align="left"):
    return {"field": field, "label": label, "align": align}

class GenericListView(LoginRequiredMixin, PermissionRequiredMixin, SortSearchListMixin, ListView):
    template_name = "ui/list.html"
    paginate_by = 20

    title = ""
    columns = []
    search_placeholder = "Поиск"
    sort_options = [("id", "ID")]
    add_url_name = None
    edit_url_name = None
    delete_url_name = None


    add_perm = None
    change_perm = None
    delete_perm = None

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            "title": self.title,
            "columns": self.columns,
            "search_placeholder": self.search_placeholder,
            "sort_options": self.sort_options,
            "add_url_name": self.add_url_name,
            "edit_url_name": self.edit_url_name,
            "delete_url_name": self.delete_url_name,

            "perms_ok_add": bool(self.add_perm and self.request.user.has_perm(self.add_perm)),
            "perms_ok_change": bool(self.change_perm and self.request.user.has_perm(self.change_perm)),
            "perms_ok_delete": bool(self.delete_perm and self.request.user.has_perm(self.delete_perm)),
        })
        return ctx

# ====== Справочники ======
class StranaListView(GenericListView):
    permission_required = "core.view_strana"
    add_perm = "core.add_strana"
    change_perm = "core.change_strana"
    delete_perm = "core.delete_strana"
    model = Strana
    title = "Страны"
    columns = [col("id", "ID"), col("nazvanie", "Название")]
    search_placeholder = "Поиск: название"
    allowed_sort = ("id", "nazvanie")
    sort_options = [("id", "ID"), ("nazvanie", "Название")]
    add_url_name = "strana_add"
    edit_url_name = "strana_edit"
    delete_url_name = "strana_delete"

    def apply_search(self, qs, q: str):
        return qs.filter(nazvanie__icontains=q)

class StranaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "core.add_strana"
    model = Strana
    form_class = StranaForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("strana_list")

class StranaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "core.change_strana"
    model = Strana
    form_class = StranaForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("strana_list")

class StranaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "core.delete_strana"
    model = Strana
    template_name = "ui/confirm_delete.html"
    success_url = reverse_lazy("strana_list")


class GorodListView(GenericListView):
    permission_required = "core.view_gorod"
    add_perm = "core.add_gorod"
    change_perm = "core.change_gorod"
    delete_perm = "core.delete_gorod"
    model = Gorod
    title = "Города"
    columns = [col("id", "ID"), col("nazvanie", "Название")]
    search_placeholder = "Поиск: название"
    allowed_sort = ("id", "nazvanie")
    sort_options = [("id", "ID"), ("nazvanie", "Название")]
    add_url_name = "gorod_add"
    edit_url_name = "gorod_edit"
    delete_url_name = "gorod_delete"

    def apply_search(self, qs, q: str):
        return qs.filter(nazvanie__icontains=q)

class GorodCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "core.add_gorod"
    model = Gorod
    form_class = GorodForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("gorod_list")

class GorodUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "core.change_gorod"
    model = Gorod
    form_class = GorodForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("gorod_list")

class GorodDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "core.delete_gorod"
    model = Gorod
    template_name = "ui/confirm_delete.html"
    success_url = reverse_lazy("gorod_list")


class UlitsaListView(GenericListView):
    permission_required = "core.view_ulitsa"
    add_perm = "core.add_ulitsa"
    change_perm = "core.change_ulitsa"
    delete_perm = "core.delete_ulitsa"
    model = Ulitsa
    title = "Улицы"
    columns = [col("id", "ID"), col("nazvanie", "Название")]
    search_placeholder = "Поиск: название"
    allowed_sort = ("id", "nazvanie")
    sort_options = [("id", "ID"), ("nazvanie", "Название")]
    add_url_name = "ulitsa_add"
    edit_url_name = "ulitsa_edit"
    delete_url_name = "ulitsa_delete"

    def apply_search(self, qs, q: str):
        return qs.filter(nazvanie__icontains=q)

class UlitsaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "core.add_ulitsa"
    model = Ulitsa
    form_class = UlitsaForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("ulitsa_list")

class UlitsaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "core.change_ulitsa"
    model = Ulitsa
    form_class = UlitsaForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("ulitsa_list")

class UlitsaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "core.delete_ulitsa"
    model = Ulitsa
    template_name = "ui/confirm_delete.html"
    success_url = reverse_lazy("ulitsa_list")

class GruppaTovarovListView(GenericListView):
    permission_required = "core.view_gruppatovarov"
    add_perm = "core.add_gruppatovarov"
    change_perm = "core.change_gruppatovarov"
    delete_perm = "core.delete_gruppatovarov"
    model = GruppaTovarov
    title = "Группы товаров"
    columns = [col("id", "ID"), col("nazvanie", "Название")]
    search_placeholder = "Поиск: название"
    allowed_sort = ("id", "nazvanie")
    sort_options = [("id", "ID"), ("nazvanie", "Название")]
    add_url_name = "gruppa_add"
    edit_url_name = "gruppa_edit"
    delete_url_name = "gruppa_delete"

    def apply_search(self, qs, q: str):
        return qs.filter(nazvanie__icontains=q)


class GruppaTovarovCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "core.add_gruppatovarov"
    model = GruppaTovarov
    form_class = GruppaTovarovForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("gruppa_list")


class GruppaTovarovUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "core.change_gruppatovarov"
    model = GruppaTovarov
    form_class = GruppaTovarovForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("gruppa_list")


class GruppaTovarovDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "core.delete_gruppatovarov"
    model = GruppaTovarov
    template_name = "ui/confirm_delete.html"
    success_url = reverse_lazy("gruppa_list")


class EdinitsaIzmereniyaListView(GenericListView):
    permission_required = "core.view_edinitsaizmereniya"
    add_perm = "core.add_edinitsaizmereniya"
    change_perm = "core.change_edinitsaizmereniya"
    delete_perm = "core.delete_edinitsaizmereniya"
    model = EdinitsaIzmereniya
    title = "Единицы измерения"
    columns = [col("id", "ID"), col("nazvanie", "Название")]
    search_placeholder = "Поиск: название"
    allowed_sort = ("id", "nazvanie")
    sort_options = [("id", "ID"), ("nazvanie", "Название")]
    add_url_name = "edinitsa_add"
    edit_url_name = "edinitsa_edit"
    delete_url_name = "edinitsa_delete"

    def apply_search(self, qs, q: str):
        return qs.filter(nazvanie__icontains=q)


class EdinitsaIzmereniyaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "core.add_edinitsaizmereniya"
    model = EdinitsaIzmereniya
    form_class = EdinitsaIzmereniyaForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("edinitsa_list")


class EdinitsaIzmereniyaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "core.change_edinitsaizmereniya"
    model = EdinitsaIzmereniya
    form_class = EdinitsaIzmereniyaForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("edinitsa_list")


class EdinitsaIzmereniyaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "core.delete_edinitsaizmereniya"
    model = EdinitsaIzmereniya
    template_name = "ui/confirm_delete.html"
    success_url = reverse_lazy("edinitsa_list")


class BankListView(GenericListView):
    permission_required = "core.view_bank"
    add_perm = "core.add_bank"
    change_perm = "core.change_bank"
    delete_perm = "core.delete_bank"
    model = Bank
    title = "Банки"
    columns = [
        col("id", "ID"),
        col("nazvanie", "Название"),
        col("inn", "ИНН"),
        col("bik", "БИК"),
        col("nomer_korrespondentnogo_scheta", "Корр. счёт"),
    ]
    search_placeholder = "Поиск: название/ИНН/БИК"
    allowed_sort = ("id", "nazvanie", "inn", "bik")
    sort_options = [("id", "ID"), ("nazvanie", "Название"), ("inn", "ИНН"), ("bik", "БИК")]
    add_url_name = "bank_add"
    edit_url_name = "bank_edit"
    delete_url_name = "bank_delete"

    def apply_search(self, qs, q: str):
        return qs.filter(
            Q(nazvanie__icontains=q) | Q(inn__icontains=q) | Q(bik__icontains=q)
        )


class BankCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "core.add_bank"
    model = Bank
    form_class = BankForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("bank_list")


class BankUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "core.change_bank"
    model = Bank
    form_class = BankForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("bank_list")


class BankDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "core.delete_bank"
    model = Bank
    template_name = "ui/confirm_delete.html"
    success_url = reverse_lazy("bank_list")


class DolzhnostListView(GenericListView):
    permission_required = "core.view_dolzhnost"
    add_perm = "core.add_dolzhnost"
    change_perm = "core.change_dolzhnost"
    delete_perm = "core.delete_dolzhnost"
    model = Dolzhnost
    title = "Должности"
    columns = [col("id", "ID"), col("nazvanie", "Название")]
    search_placeholder = "Поиск: название"
    allowed_sort = ("id", "nazvanie")
    sort_options = [("id", "ID"), ("nazvanie", "Название")]
    add_url_name = "dolzhnost_add"
    edit_url_name = "dolzhnost_edit"
    delete_url_name = "dolzhnost_delete"

    def apply_search(self, qs, q: str):
        return qs.filter(nazvanie__icontains=q)


class DolzhnostCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "core.add_dolzhnost"
    model = Dolzhnost
    form_class = DolzhnostForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("dolzhnost_list")


class DolzhnostUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "core.change_dolzhnost"
    model = Dolzhnost
    form_class = DolzhnostForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("dolzhnost_list")


class DolzhnostDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "core.delete_dolzhnost"
    model = Dolzhnost
    template_name = "ui/confirm_delete.html"
    success_url = reverse_lazy("dolzhnost_list")

# ====== Кадровые справочники ======

class ProfessiyaListView(GenericListView):
    permission_required = "core.view_professiya"
    add_perm = "core.add_professiya"
    change_perm = "core.change_professiya"
    delete_perm = "core.delete_professiya"
    model = Professiya
    title = "Профессии"
    columns = [col("id", "ID"), col("nazvanie", "Название")]
    search_placeholder = "Поиск: название"
    allowed_sort = ("id", "nazvanie")
    sort_options = [("id", "ID"), ("nazvanie", "Название")]
    add_url_name = "professiya_add"
    edit_url_name = "professiya_edit"
    delete_url_name = "professiya_delete"

    def apply_search(self, qs, q: str):
        return qs.filter(nazvanie__icontains=q)

class ProfessiyaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "core.add_professiya"
    model = Professiya
    form_class = ProfessiyaForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("professiya_list")

class ProfessiyaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "core.change_professiya"
    model = Professiya
    form_class = ProfessiyaForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("professiya_list")

class ProfessiyaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "core.delete_professiya"
    model = Professiya
    template_name = "ui/confirm_delete.html"
    success_url = reverse_lazy("professiya_list")


class SpecialnostListView(GenericListView):
    permission_required = "core.view_specialnost"
    add_perm = "core.add_specialnost"
    change_perm = "core.change_specialnost"
    delete_perm = "core.delete_specialnost"
    model = Specialnost
    title = "Специальности"
    columns = [col("id", "ID"), col("nazvanie", "Название")]
    search_placeholder = "Поиск: название"
    allowed_sort = ("id", "nazvanie")
    sort_options = [("id", "ID"), ("nazvanie", "Название")]
    add_url_name = "specialnost_add"
    edit_url_name = "specialnost_edit"
    delete_url_name = "specialnost_delete"

    def apply_search(self, qs, q: str):
        return qs.filter(nazvanie__icontains=q)

class SpecialnostCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "core.add_specialnost"
    model = Specialnost
    form_class = SpecialnostForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("specialnost_list")

class SpecialnostUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "core.change_specialnost"
    model = Specialnost
    form_class = SpecialnostForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("specialnost_list")

class SpecialnostDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "core.delete_specialnost"
    model = Specialnost
    template_name = "ui/confirm_delete.html"
    success_url = reverse_lazy("specialnost_list")


class KlassifikaciyaListView(GenericListView):
    permission_required = "core.view_klassifikaciya"
    add_perm = "core.add_klassifikaciya"
    change_perm = "core.change_klassifikaciya"
    delete_perm = "core.delete_klassifikaciya"
    model = Klassifikaciya
    title = "Квалификации"
    columns = [col("id", "ID"), col("nazvanie", "Название")]
    search_placeholder = "Поиск: название"
    allowed_sort = ("id", "nazvanie")
    sort_options = [("id", "ID"), ("nazvanie", "Название")]
    add_url_name = "klassifikaciya_add"
    edit_url_name = "klassifikaciya_edit"
    delete_url_name = "klassifikaciya_delete"

    def apply_search(self, qs, q: str):
        return qs.filter(nazvanie__icontains=q)

class KlassifikaciyaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "core.add_klassifikaciya"
    model = Klassifikaciya
    form_class = KlassifikaciyaForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("klassifikaciya_list")

class KlassifikaciyaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "core.change_klassifikaciya"
    model = Klassifikaciya
    form_class = KlassifikaciyaForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("klassifikaciya_list")

class KlassifikaciyaDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "core.delete_klassifikaciya"
    model = Klassifikaciya
    template_name = "ui/confirm_delete.html"
    success_url = reverse_lazy("klassifikaciya_list")


class StruktPodrazdelenieListView(GenericListView):
    permission_required = "core.view_struktpodrazdelenie"
    add_perm = "core.add_struktpodrazdelenie"
    change_perm = "core.change_struktpodrazdelenie"
    delete_perm = "core.delete_struktpodrazdelenie"
    model = StruktPodrazdelenie
    title = "Структурные подразделения"
    columns = [col("id", "ID"), col("nazvanie", "Название")]
    search_placeholder = "Поиск: название"
    allowed_sort = ("id", "nazvanie")
    sort_options = [("id", "ID"), ("nazvanie", "Название")]
    add_url_name = "strukt_add"
    edit_url_name = "strukt_edit"
    delete_url_name = "strukt_delete"

    def apply_search(self, qs, q: str):
        return qs.filter(nazvanie__icontains=q)

class StruktPodrazdelenieCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "core.add_struktpodrazdelenie"
    model = StruktPodrazdelenie
    form_class = StruktPodrazdelenieForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("strukt_list")

class StruktPodrazdelenieUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "core.change_struktpodrazdelenie"
    model = StruktPodrazdelenie
    form_class = StruktPodrazdelenieForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("strukt_list")

class StruktPodrazdelenieDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "core.delete_struktpodrazdelenie"
    model = StruktPodrazdelenie
    template_name = "ui/confirm_delete.html"
    success_url = reverse_lazy("strukt_list")
# ===== Кадровые документы =====

class MestoRabotyListView(GenericListView):
    permission_required = "core.view_mestoraboty"
    add_perm = "core.add_mestoraboty"
    change_perm = "core.change_mestoraboty"
    delete_perm = "core.delete_mestoraboty"
    model = MestoRaboty
    title = "Места работы"
    columns = [
        col("id", "ID"),
        col("nazvanie", "Название"),
        col("id_strana", "Страна"),
        col("id_gorod", "Город"),
        col("id_ulica", "Улица"),
        col("nomer_doma", "Дом"),
    ]
    search_placeholder = "Поиск: название/город"
    allowed_sort = ("id", "nazvanie")
    sort_options = [("id", "ID"), ("nazvanie", "Название")]
    add_url_name = "mestoraboty_add"
    edit_url_name = "mestoraboty_edit"
    delete_url_name = "mestoraboty_delete"

    def apply_search(self, qs, q: str):
        return qs.filter(Q(nazvanie__icontains=q) | Q(id_gorod__nazvanie__icontains=q))

class MestoRabotyCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "core.add_mestoraboty"
    model = MestoRaboty
    form_class = MestoRabotyForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("mestoraboty_list")

class MestoRabotyUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "core.change_mestoraboty"
    model = MestoRaboty
    form_class = MestoRabotyForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("mestoraboty_list")

class MestoRabotyDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "core.delete_mestoraboty"
    model = MestoRaboty
    template_name = "ui/confirm_delete.html"
    success_url = reverse_lazy("mestoraboty_list")


class ZapisiTrudKnizhkeListView(ScopeByMagazinMixin, GenericListView):
    permission_required = "core.view_zapisitrudknizhke"
    add_perm = "core.add_zapisitrudknizhke"
    change_perm = "core.change_zapisitrudknizhke"
    delete_perm = "core.delete_zapisitrudknizhke"
    model = ZapisiTrudKnizhke
    title = "Трудовая книжка (кадровые события)"
    columns = [
        col("id", "ID"),
        col("id_rabotnika", "Работник"),
        col("vid_dokumenta", "Вид документа"),
        col("vid_meropriyatiya", "Мероприятие"),
        col("data", "Дата"),
        col("nomer", "Номер"),
        col("id_dolzhnosti", "Должность"),
        col("id_mesto_raboty", "Место работы"),
    ]
    search_placeholder = "Поиск: работник / документ / место"
    allowed_sort = ("id", "data", "vid_dokumenta")
    sort_options = [("id", "ID"), ("data", "Дата"), ("vid_dokumenta", "Вид")]
    add_url_name = "trud_add"
    edit_url_name = "trud_edit"
    delete_url_name = "trud_delete"

    def get_queryset(self):
        qs = super().get_queryset().select_related("id_rabotnika", "id_mesto_raboty", "id_dolzhnosti")
        return self.scope_qs(qs, "id_rabotnika__id_otdela__id_magazin")

    def apply_search(self, qs, q: str):
        return qs.filter(
            Q(id_rabotnika__familiya__icontains=q)
            | Q(id_rabotnika__imya__icontains=q)
            | Q(id_rabotnika__otchestvo__icontains=q)
            | Q(nomer__icontains=q)
            | Q(id_mesto_raboty__nazvanie__icontains=q)
        )

class ZapisiTrudKnizhkeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "core.add_zapisitrudknizhke"
    model = ZapisiTrudKnizhke
    form_class = ZapisiTrudKnizhkeForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("trud_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

class ZapisiTrudKnizhkeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, ScopeByMagazinMixin, UpdateView):
    permission_required = "core.change_zapisitrudknizhke"
    model = ZapisiTrudKnizhke
    form_class = ZapisiTrudKnizhkeForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("trud_list")

    def get_queryset(self):
        return self.scope_qs(super().get_queryset(), "id_rabotnika__id_otdela__id_magazin")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

class ZapisiTrudKnizhkeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, ScopeByMagazinMixin, DeleteView):
    permission_required = "core.delete_zapisitrudknizhke"
    model = ZapisiTrudKnizhke
    template_name = "ui/confirm_delete.html"
    success_url = reverse_lazy("trud_list")

    def get_queryset(self):
        return self.scope_qs(super().get_queryset(), "id_rabotnika__id_otdela__id_magazin")



class OtdelListView(ScopeByMagazinMixin, GenericListView):
    permission_required = "core.view_otdel"
    add_perm = "core.add_otdel"
    change_perm = "core.change_otdel"
    delete_perm = "core.delete_otdel"
    model = Otdel
    title = "Отделы"
    columns = [col("id", "ID"), col("nazvanie", "Название"), col("id_gruppa_tovarov", "Группа товаров")]
    search_placeholder = "Поиск: название/группа"
    allowed_sort = ("id", "nazvanie")
    sort_options = [("id", "ID"), ("nazvanie", "Название")]
    add_url_name = "otdel_add"
    edit_url_name = "otdel_edit"
    delete_url_name = "otdel_delete"

    def apply_search(self, qs, q: str):
        return qs.filter(Q(nazvanie__icontains=q) | Q(id_gruppa_tovarov__nazvanie__icontains=q))

    def get_queryset(self):
        qs = super().get_queryset()
        return self.scope_qs(qs, "id_magazin")


class OtdelCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "core.add_otdel"
    model = Otdel
    form_class = OtdelForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("otdel_list")


class OtdelUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "core.change_otdel"
    model = Otdel
    form_class = OtdelForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("otdel_list")


class OtdelDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "core.delete_otdel"
    model = Otdel
    template_name = "ui/confirm_delete.html"
    success_url = reverse_lazy("otdel_list")

# ====== Бизнес-сущности ======

class MagazinListView(GenericListView):
    permission_required = "core.view_magazin"
    add_perm = "core.add_magazin"
    change_perm = "core.change_magazin"
    delete_perm = "core.delete_magazin"
    model = Magazin
    title = "Магазины"
    columns = [
        col("id", "ID"),
        col("nazvanie", "Название"),
        col("familiya_direktora", "Фамилия директора"),
        col("imya_direktora", "Имя директора"),
        col("otchestvo_direktora", "Отчество директора"),
        col("id_strana", "Страна"),
        col("id_gorod", "Город"),
        col("id_ulica", "Улица"),
        col("nomer_doma", "Дом"),
    ]
    search_placeholder = "Поиск: название / директор / город"
    allowed_sort = ("id", "nazvanie")
    sort_options = [("id", "ID"), ("nazvanie", "Название")]
    add_url_name = "magazin_add"
    edit_url_name = "magazin_edit"
    delete_url_name = "magazin_delete"

    def apply_search(self, qs, q: str):
        return qs.filter(
            Q(nazvanie__icontains=q)
            | Q(familiya_direktora__icontains=q)
            | Q(id_gorod__nazvanie__icontains=q)
        )

class MagazinCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "core.add_magazin"
    model = Magazin
    form_class = MagazinForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("magazin_list")

class MagazinUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "core.change_magazin"
    model = Magazin
    form_class = MagazinForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("magazin_list")

class MagazinDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "core.delete_magazin"
    model = Magazin
    template_name = "ui/confirm_delete.html"
    success_url = reverse_lazy("magazin_list")


class PostavshchikListView(GenericListView):
    permission_required = "core.view_postavshchik"
    add_perm = "core.add_postavshchik"
    change_perm = "core.change_postavshchik"
    delete_perm = "core.delete_postavshchik"
    model = Postavshchik
    title = "Поставщики"
    columns = [
        col("id", "ID"),
        col("nazvanie", "Название"),
        col("abreviatura", "Аббр."),
        col("kod_po_ok", "Код ОК"),
        col("nomer_telefona", "Телефон"),
        col("id_bank", "Банк"),
        col("id_gorod", "Город"),
    ]
    search_placeholder = "Поиск: название / телефон / банк / город"
    allowed_sort = ("id", "nazvanie")
    sort_options = [("id", "ID"), ("nazvanie", "Название")]
    add_url_name = "postavshchik_add"
    edit_url_name = "postavshchik_edit"
    delete_url_name = "postavshchik_delete"

    def apply_search(self, qs, q: str):
        return qs.filter(
            Q(nazvanie__icontains=q)
            | Q(nomer_telefona__icontains=q)
            | Q(id_bank__nazvanie__icontains=q)
            | Q(id_gorod__nazvanie__icontains=q)
        )

class PostavshchikCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "core.add_postavshchik"
    model = Postavshchik
    form_class = PostavshchikForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("postavshchik_list")

class PostavshchikUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "core.change_postavshchik"
    model = Postavshchik
    form_class = PostavshchikForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("postavshchik_list")

class PostavshchikDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "core.delete_postavshchik"
    model = Postavshchik
    template_name = "ui/confirm_delete.html"
    success_url = reverse_lazy("postavshchik_list")


class RabotnikListView(ScopeByMagazinMixin, GenericListView):
    permission_required = "core.view_rabotnik"
    add_perm = "core.add_rabotnik"
    change_perm = "core.change_rabotnik"
    delete_perm = "core.delete_rabotnik"
    model = Rabotnik
    title = "Работники"
    columns = [
        col("id", "ID"),
        col("familiya", "Фамилия"),
        col("imya", "Имя"),
        col("otchestvo", "Отчество"),
        col("pol", "Пол"),
        col("data_rozhdeniya", "Дата рождения"),
        col("id_dolzhnost", "Должность"),
        col("id_otdela", "Отдел"),
    ]
    search_placeholder = "Поиск: ФИО / должность / отдел"
    allowed_sort = ("id", "familiya", "data_rozhdeniya")
    sort_options = [("id", "ID"), ("familiya", "Фамилия"), ("data_rozhdeniya", "Дата рождения")]
    add_url_name = "rabotnik_add"
    edit_url_name = "rabotnik_edit"
    delete_url_name = "rabotnik_delete"

    def apply_search(self, qs, q: str):
        return qs.filter(
            Q(familiya__icontains=q)
            | Q(imya__icontains=q)
            | Q(otchestvo__icontains=q)
            | Q(id_dolzhnost__nazvanie__icontains=q)
            | Q(id_otdela__nazvanie__icontains=q)
        )

    def get_queryset(self):
        qs = super().get_queryset()
        mid = self.get_magazin_id()
        if mid is None:
            return qs  # владелец сети
        if not mid:
            return qs.none()
        return qs.filter(id_otdela__id_magazin_id=mid)
class RabotnikCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "core.add_rabotnik"
    model = Rabotnik
    form_class = RabotnikForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("rabotnik_list")

class RabotnikUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "core.change_rabotnik"
    model = Rabotnik
    form_class = RabotnikForm
    template_name = "ui/form.html"
    success_url = reverse_lazy("rabotnik_list")

class RabotnikDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "core.delete_rabotnik"
    model = Rabotnik
    template_name = "ui/confirm_delete.html"
    success_url = reverse_lazy("rabotnik_list")



class AnalyticsView(LoginRequiredMixin, PermissionRequiredMixin, ScopeByMagazinMixin, TemplateView):
    permission_required = "core.view_vyruchka"
    template_name = "ui/analytics.html"

    def _parse_date(self, s: str):
        try:
            y, m, d = map(int, (s or "").split("-"))
            return date(y, m, d)
        except Exception:
            return None

    def _date_range(self):
        to_s = self.request.GET.get("to") or ""
        from_s = self.request.GET.get("from") or ""
        to_d = self._parse_date(to_s) or date.today()
        from_d = self._parse_date(from_s) or (to_d - timedelta(days=30))
        return from_d, to_d

    def _selected_magazin_id(self) -> int:
        """
        Для владельца сети разрешаем выбрать магазин через GET ?magazin=ID (0 = все).
        Для остальных — фильтр по магазину пользователя (скоупинг) и это поле не учитываем.
        """
        if not self.is_network_owner():
            return 0
        raw = (self.request.GET.get("magazin") or "").strip()
        try:
            return int(raw) if raw else 0
        except Exception:
            return 0

    def _amount_expr(self):
        """
        Сумма строки продажи:
        - если в строке заполнено `summa` — берём её
        - иначе считаем kolichestvo * cena_prodazhi (сначала из строки, иначе из товара)
        """
        qty = Coalesce(F("kolichestvo"), 0)
        price = Coalesce(F("cena_prodazhi"), F("id_tovar__cena_prodazhi"), Decimal("0"))
        calc = ExpressionWrapper(qty * price, output_field=DecimalField(max_digits=14, decimal_places=2))
        return Coalesce(F("summa"), calc, Decimal("0"))

    def _base_tvv(self, from_d, to_d):
        qs = TovarVyruchka.objects.filter(
            id_vyruchka__data__isnull=False,
            id_vyruchka__data__range=(from_d, to_d),
            id_vyruchka__id_magazin__isnull=False,
        )

        qs = self.scope_qs(qs, "id_vyruchka__id_magazin")

        sel = self._selected_magazin_id()
        if sel:
            qs = qs.filter(id_vyruchka__id_magazin_id=sel)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        tab = (self.request.GET.get("tab") or "daily").strip()
        if tab not in ("daily", "stores", "sellers"):
            tab = "daily"

        from_d, to_d = self._date_range()
        amount_expr = self._amount_expr()
        tvv = self._base_tvv(from_d, to_d)

        # список магазинов для выпадашки (только владельцу сети)
        magazins = []
        selected_magazin = 0
        if self.is_network_owner():
            magazins = list(Magazin.objects.all().order_by("nazvanie"))
            selected_magazin = self._selected_magazin_id()

        # -------- Динамика (по дням)
        daily = list(
            tvv.values("id_vyruchka__data")
               .annotate(
                    qty=Coalesce(Sum("kolichestvo"), 0),
                    amount=Coalesce(Sum(amount_expr), Decimal("0")),
               )
               .order_by("id_vyruchka__data")
        )

        total_sum = sum((row["amount"] or Decimal("0") for row in daily), Decimal("0"))
        days_count = len(daily)
        avg_day = (total_sum / days_count) if days_count else Decimal("0")

        # -------- Топ товаров
        top_qty = list(
            tvv.values("id_tovar__nazvanie")
               .annotate(qty=Coalesce(Sum("kolichestvo"), 0))
               .order_by("-qty")[:10]
        )

        top_amount = list(
            tvv.values("id_tovar__nazvanie")
               .annotate(amount=Coalesce(Sum(amount_expr), Decimal("0")))
               .order_by("-amount")[:10]
        )

        # -------- По магазинам
        by_store = list(
            tvv.values("id_vyruchka__id_magazin__nazvanie")
               .annotate(
                    qty=Coalesce(Sum("kolichestvo"), 0),
                    amount=Coalesce(Sum(amount_expr), Decimal("0")),
                    checks=Count("id_vyruchka", distinct=True),
               )
               .order_by("-amount")
        )

        # -------- По продавцам
        by_seller = list(
            tvv.values(
                "id_vyruchka__id_magazin__nazvanie",
                "id_vyruchka__id_rabotnik__familiya",
                "id_vyruchka__id_rabotnik__imya",
                "id_vyruchka__id_rabotnik__otchestvo",
            )
            .annotate(
                qty=Coalesce(Sum("kolichestvo"), 0),
                amount=Coalesce(Sum(amount_expr), Decimal("0")),
                checks=Count("id_vyruchka", distinct=True),
            )
            .order_by("-amount")
        )

        ctx.update({
            "tab": tab,
            "from": from_d.isoformat(),
            "to": to_d.isoformat(),

            "magazins": magazins,
            "selected_magazin": selected_magazin,

            "daily": daily,
            "labels": [r["id_vyruchka__data"].isoformat() for r in daily],
            "values": [float(r["amount"] or 0) for r in daily],
            "total_sum": total_sum,
            "avg_day": avg_day,
            "top_qty": top_qty,
            "top_amount": top_amount,

            "by_store": by_store,
            "by_seller": by_seller,
        })
        return ctx


# ----------------- exports -----------------

def _parse_date_q(s: str):
    try:
        y, m, d = map(int, (s or "").split("-"))
        return date(y, m, d)
    except Exception:
        return None


def _daterange_from_request(request):
    to_d = _parse_date_q(request.GET.get("to") or "") or date.today()
    from_d = _parse_date_q(request.GET.get("from") or "") or (to_d - timedelta(days=30))
    return from_d, to_d


def _is_network_owner(user) -> bool:
    return bool(user.is_superuser or user.groups.filter(name="Владелец сети").exists())


def _scoped_tvv(request, from_d, to_d):
    tvv = TovarVyruchka.objects.filter(
        id_vyruchka__data__isnull=False,
        id_vyruchka__data__range=(from_d, to_d),
        id_vyruchka__id_magazin__isnull=False,
    )

    if _is_network_owner(request.user):
        # владелец сети может выбрать магазин
        raw = (request.GET.get("magazin") or "").strip()
        try:
            sel = int(raw) if raw else 0
        except Exception:
            sel = 0
        if sel:
            tvv = tvv.filter(id_vyruchka__id_magazin_id=sel)
        return tvv

    # не владелец: режем по магазину из профиля
    prof = getattr(request.user, "profile", None)
    mid = getattr(prof, "id_magazin_id", None) or 0
    if not mid:
        return tvv.none()
    return tvv.filter(id_vyruchka__id_magazin_id=mid)


def _amount_expr():
    qty = Coalesce(F("kolichestvo"), 0)
    price = Coalesce(F("cena_prodazhi"), F("id_tovar__cena_prodazhi"), Decimal("0"))
    calc = ExpressionWrapper(qty * price, output_field=DecimalField(max_digits=14, decimal_places=2))
    return Coalesce(F("summa"), calc, Decimal("0"))


def analytics_export_csv(request):
    mode = (request.GET.get("mode") or "daily").strip()
    if mode not in ("daily", "stores", "sellers"):
        mode = "daily"

    from_d, to_d = _daterange_from_request(request)
    tvv = _scoped_tvv(request, from_d, to_d)
    amount_expr = _amount_expr()

    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    w = csv.writer(resp)

    if mode == "daily":
        resp["Content-Disposition"] = 'attachment; filename="analytics_daily.csv"'
        rows = list(
            tvv.values("id_vyruchka__data")
               .annotate(qty=Coalesce(Sum("kolichestvo"), 0), amount=Coalesce(Sum(amount_expr), Decimal("0")))
               .order_by("id_vyruchka__data")
        )
        w.writerow(["date", "qty", "amount"])
        for r in rows:
            w.writerow([r["id_vyruchka__data"].isoformat(), r["qty"], r["amount"]])
        return resp

    if mode == "stores":
        resp["Content-Disposition"] = 'attachment; filename="analytics_by_store.csv"'
        rows = list(
            tvv.values("id_vyruchka__id_magazin__nazvanie")
               .annotate(
                    checks=Count("id_vyruchka", distinct=True),
                    qty=Coalesce(Sum("kolichestvo"), 0),
                    amount=Coalesce(Sum(amount_expr), Decimal("0")),
               )
               .order_by("-amount")
        )
        w.writerow(["magazin", "checks", "qty", "amount"])
        for r in rows:
            w.writerow([r["id_vyruchka__id_magazin__nazvanie"], r["checks"], r["qty"], r["amount"]])
        return resp

    # sellers
    resp["Content-Disposition"] = 'attachment; filename="analytics_by_seller.csv"'
    rows = list(
        tvv.values(
            "id_vyruchka__id_magazin__nazvanie",
            "id_vyruchka__id_rabotnik__familiya",
            "id_vyruchka__id_rabotnik__imya",
            "id_vyruchka__id_rabotnik__otchestvo",
        )
        .annotate(
            checks=Count("id_vyruchka", distinct=True),
            qty=Coalesce(Sum("kolichestvo"), 0),
            amount=Coalesce(Sum(amount_expr), Decimal("0")),
        )
        .order_by("-amount")
    )
    w.writerow(["magazin", "seller", "checks", "qty", "amount"])
    for r in rows:
        fio = " ".join(x for x in [
            r["id_vyruchka__id_rabotnik__familiya"],
            r["id_vyruchka__id_rabotnik__imya"],
            r["id_vyruchka__id_rabotnik__otchestvo"],
        ] if x)
        w.writerow([r["id_vyruchka__id_magazin__nazvanie"], fio, r["checks"], r["qty"], r["amount"]])
    return resp




class SqlConsoleView(LoginRequiredMixin, TemplateView):
    template_name = "ui/sql_console.html"


    FORBIDDEN_RE = re.compile(
        r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|vacuum|analyze)\b",
        re.IGNORECASE,
    )

    def _allowed(self) -> bool:
        u = self.request.user
        return u.is_superuser or u.has_perm("core.sql_console")

    def _sanitize_for_check(self, sql: str) -> str:

        s = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
        s = re.sub(r"--.*?$", " ", s, flags=re.M)
        s = re.sub(r"'(?:''|[^'])*'", "''", s)  # строки '...'
        return s

    def _is_single_statement(self, sql: str) -> bool:
        parts = [p.strip() for p in sql.split(";") if p.strip()]
        return len(parts) <= 1

    def get(self, request, *args, **kwargs):
        if not self._allowed():
            return self.render_to_response(
                {"sql": "", "columns": [], "rows": [], "error": "Нет доступа к SQL-консоли"},
                status=403,
            )
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not self._allowed():
            return self.render_to_response(
                {"sql": request.POST.get("sql", ""), "columns": [], "rows": [], "error": "Нет доступа к SQL-консоли"},
                status=403,
            )

        sql = (request.POST.get("sql") or "").strip()
        error = None
        columns, rows = [], []

        if not sql:
            error = "Пустой запрос"
        elif not self._is_single_statement(sql):
            error = "Разрешён только один SQL-запрос за раз (без нескольких команд через ;)"
        else:
            check = self._sanitize_for_check(sql).strip().lower()
            first = (check.split(None, 1) or [""])[0]

            # Разрешаем SELECT и WITH (CTE). Можно добавлять EXPLAIN при желании.
            if first not in ("select", "with"):
                error = "Разрешены только SELECT-запросы (в т.ч. WITH ... SELECT ...)"
            elif self.FORBIDDEN_RE.search(check):
                error = "Запрос содержит запрещённые ключевые слова (DDL/DML)"
            else:
                try:
                    with connection.cursor() as cur:
                        cur.execute(sql)
                        columns = [c[0] for c in (cur.description or [])]
                        rows = [list(map(lambda v: "" if v is None else str(v), r))
                                for r in cur.fetchmany(200)]
                except Exception as e:
                    error = str(e)

        return self.render_to_response({"sql": sql, "columns": columns, "rows": rows, "error": error})



class UserListView(LoginRequiredMixin, OwnerOnlyMixin, ListView):
    model = User
    template_name = "ui/user_list.html"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset().order_by("username")
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q))
        return qs


class UserCreateView(LoginRequiredMixin, OwnerOnlyMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = "ui/user_form.html"
    success_url = reverse_lazy("user_list")


class UserUpdateView(LoginRequiredMixin, OwnerOnlyMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = "ui/user_form.html"
    success_url = reverse_lazy("user_list")


class UserDeleteView(LoginRequiredMixin, OwnerOnlyMixin, DeleteView):
    model = User
    template_name = "ui/confirm_delete.html"
    success_url = reverse_lazy("user_list")

def error_404(request, exception):
    return render(request, "404.html", status=404)

def error_403(request, exception=None):
    return render(request, "403.html", status=403)

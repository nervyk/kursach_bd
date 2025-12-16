from django.db.models import Q
from django.http import HttpResponseForbidden

class OwnerOnlyMixin:
    def dispatch(self, request, *args, **kwargs):
        u = request.user
        ok = u.is_superuser or u.groups.filter(name="Владелец сети").exists()
        if not ok:
            return HttpResponseForbidden("Forbidden")
        return super().dispatch(request, *args, **kwargs)

class SortSearchListMixin:
    search_param = "q"
    sort_param = "sort"
    dir_param = "dir"

    allowed_sort = ("id",)
    default_sort = "id"

    def get_search_q(self) -> str:
        return (self.request.GET.get(self.search_param) or "").strip()

    def get_sort(self):
        sort = (self.request.GET.get(self.sort_param) or self.default_sort or "id").strip()
        direction = (self.request.GET.get(self.dir_param) or "asc").strip().lower()

        # поддержка старого формата sort=-field
        if sort.startswith("-"):
            sort = sort[1:]
            direction = "desc"

        if sort not in self.allowed_sort:
            sort = self.default_sort or "id"

        if direction not in ("asc", "desc"):
            direction = "asc"

        return sort, direction

    def apply_search(self, qs, q: str):
        return qs

    def get_queryset(self):
        qs = super().get_queryset()

        q = self.get_search_q()
        if q:
            qs = self.apply_search(qs, q)

        sort, direction = self.get_sort()
        order = f"-{sort}" if direction == "desc" else sort
        return qs.order_by(order)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.get_search_q()
        ctx["sort"], ctx["dir"] = self.get_sort()
        return ctx


class ScopeByMagazinMixin:
    """
    Ограничивает данные по магазину пользователя.
    Владелец сети и superuser видят всё.
    Остальные видят только свой магазин из user.profile.id_magazin_id.
    """

    def is_network_owner(self) -> bool:
        u = self.request.user
        return u.is_superuser or u.groups.filter(name="Владелец сети").exists()

    def get_magazin_id(self):
        """
        None -> владелец сети (нет ограничения)
        0/False -> магазин не назначен (режем доступ: qs.none())
        int -> конкретный магазин
        """
        if self.is_network_owner():
            return None

        prof = getattr(self.request.user, "profile", None)
        mid = getattr(prof, "id_magazin_id", None)
        return mid or 0

    def scope_qs(self, qs, field_name="id_magazin"):
        """
        field_name — имя FK поля в модели (например id_magazin).
        """
        mid = self.get_magazin_id()
        if mid is None:
            return qs                # владелец сети
        if not mid:
            return qs.none()         # магазин не назначен => ничего не показываем
        return qs.filter(**{f"{field_name}_id": mid})
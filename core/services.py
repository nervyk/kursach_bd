from django.db import transaction
from django.db.models import F
from core.models import Zayavka, ZayavkaItem, Tovar, MagazinTovar
from django.db import transaction
from django.db.models import F
from django.db.models.functions import Coalesce
from .models import MagazinTovar, TovarVyruchka, Vyruchka
from django.db.models.functions import Coalesce

class ZayavkaApproveError(Exception):
    pass

@transaction.atomic
def approve_zayavka(z: Zayavka):
    z = Zayavka.objects.select_for_update().get(pk=z.pk)

    if z.status == Zayavka.Status.APPROVED:
        return
    if z.status != Zayavka.Status.SENT:
        raise ZayavkaApproveError("Проведение возможно только из статуса 'Отправлена'")

    items = list(ZayavkaItem.objects.select_for_update().filter(id_zayavka=z).select_related("id_tovar"))
    if not items:
        raise ZayavkaApproveError("В заявке нет позиций")

    # проверка остатков на центральном складе
    for it in items:
        qty = int(it.kolichestvo or 0)
        if qty <= 0:
            continue
        t = it.id_tovar
        stock = int(t.kolichestvo_na_sklade or 0)
        if stock < qty:
            raise ZayavkaApproveError(f"Недостаточно товара '{t.nazvanie}' на центральном складе")

    # списание/зачисление
    for it in items:
        qty = int(it.kolichestvo or 0)
        if qty <= 0:
            continue

        Tovar.objects.filter(pk=it.id_tovar_id).update(
            kolichestvo_na_sklade=Coalesce(F("kolichestvo_na_sklade"), 0) - qty
        )

        mt, _ = MagazinTovar.objects.get_or_create(
            id_magazin=z.id_magazin, id_tovar=it.id_tovar,
            defaults={"kolichestvo": 0}
        )
        MagazinTovar.objects.filter(pk=mt.pk).update(
            kolichestvo=Coalesce(F("kolichestvo"), 0) + qty
        )

    z.status = Zayavka.Status.APPROVED
    z.save(update_fields=["status"])

class StockError(Exception):
    pass

@transaction.atomic
def apply_vyruchka_stock(magazin_id: int, delta_by_tovar: dict[int, int]):
    """
    delta_by_tovar: {tovar_id: delta_qty}
    delta_qty > 0  -> СПИСАТЬ со склада магазина
    delta_qty < 0  -> ВЕРНУТЬ на склад магазина
    """
    if not magazin_id:
        return

    for tovar_id, delta in delta_by_tovar.items():
        if not delta:
            continue

        # Блокируем строку magazin_tovar на время операции
        mt = (MagazinTovar.objects
              .select_for_update()
              .filter(id_magazin_id=magazin_id, id_tovar_id=tovar_id)
              .first())

        if mt is None:
            mt = MagazinTovar.objects.create(id_magazin_id=magazin_id, id_tovar_id=tovar_id, kolichestvo=0)
            mt = (MagazinTovar.objects
                  .select_for_update()
                  .get(pk=mt.pk))

        current = int(mt.kolichestvo or 0)

        if delta > 0 and current < delta:
            raise StockError(f"Недостаточно товара на складе магазина (tovar_id={tovar_id}). Остаток={current}, нужно={delta}")

        if delta > 0:
            MagazinTovar.objects.filter(pk=mt.pk).update(
                kolichestvo=Coalesce(F("kolichestvo"), 0) - delta
            )
        else:
            MagazinTovar.objects.filter(pk=mt.pk).update(
                kolichestvo=Coalesce(F("kolichestvo"), 0) + abs(delta)
            )
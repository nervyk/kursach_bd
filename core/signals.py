from decimal import Decimal, ROUND_HALF_UP

from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from django.db.models import F
from django.db.models.functions import Coalesce
from django.db.models.signals import post_migrate
from django.contrib.auth.models import Group, Permission
from .models import Postavka, Tovar
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import UserProfile

def _qty_to_int(qty) -> int:
    """
    Приводим количество из Decimal/None к int безопасно.
    Если у тебя количество всегда целое — проблем не будет.
    """
    if qty is None:
        return 0
    if isinstance(qty, Decimal):
        return int(qty.to_integral_value(rounding=ROUND_HALF_UP))
    return int(qty)


@receiver(pre_save, sender=Postavka)
def postavka_pre_save(sender, instance: Postavka, **kwargs):
    if instance.pk:
        old = Postavka.objects.filter(pk=instance.pk).only("kolichestvo", "id_tovar").first()
        instance._old_qty_int = _qty_to_int(old.kolichestvo) if old else 0
        instance._old_tovar_id = old.id_tovar_id if old else None
    else:
        instance._old_qty_int = 0
        instance._old_tovar_id = None


@receiver(post_save, sender=Postavka)
def postavka_post_save(sender, instance: Postavka, created, **kwargs):
    new_qty = _qty_to_int(instance.kolichestvo)
    old_qty = getattr(instance, "_old_qty_int", 0)
    old_tovar_id = getattr(instance, "_old_tovar_id", None)

    # Если изменили товар у уже существующей поставки — откатываем старому товару старое количество
    if old_tovar_id and old_tovar_id != instance.id_tovar_id and old_qty:
        Tovar.objects.filter(pk=old_tovar_id).update(
            kolichestvo_na_sklade=Coalesce(F("kolichestvo_na_sklade"), 0) - old_qty
        )
        old_qty = 0

    # Докидываем разницу новому товару
    delta = new_qty - old_qty
    if delta:
        Tovar.objects.filter(pk=instance.id_tovar_id).update(
            kolichestvo_na_sklade=Coalesce(F("kolichestvo_na_sklade"), 0) + delta
        )


@receiver(pre_delete, sender=Postavka)
def postavka_pre_delete(sender, instance: Postavka, **kwargs):
    qty = _qty_to_int(instance.kolichestvo)
    if qty:
        Tovar.objects.filter(pk=instance.id_tovar_id).update(
            kolichestvo_na_sklade=Coalesce(F("kolichestvo_na_sklade"), 0) - qty
        )

ROLE_GROUPS = {
    "Владелец сети": {"all_core": True, "extra": ["sql_console", "approve_zayavka"]},

    "Директор магазина": {"models": ["magazin", "otdel", "rabotnik", "vyruchka", "zayavka", "magazintovar"],
                          "actions": ["view"], "extra": []},

    "Руководитель отдела": {"models": ["vyruchka", "rabotnik", "magazintovar"],
                            "actions": ["view"], "extra": []},

    "Заведующий складом магазина": {"models": ["zayavka", "magazintovar", "tovar"],
                                    "actions": ["view", "add", "change"], "extra": []},

    "Менеджер по закупкам": {"models": ["postavshchik", "postavka", "tovar", "zayavka"],
                             "actions": ["view", "add", "change"], "extra": ["approve_zayavka"]},

    "Бухгалтер магазина": {"models": ["rabotnik", "zapisitrudknizhke", "mestoraboty"],
                           "actions": ["view", "add", "change"], "extra": []},
}

@receiver(post_migrate)
def create_groups_and_perms(sender, **kwargs):
    # запускаем один раз после миграций core
    if sender.name != "core":
        return

    all_core_perms = Permission.objects.filter(content_type__app_label="core")

    for group_name, cfg in ROLE_GROUPS.items():
        g, _ = Group.objects.get_or_create(name=group_name)

        perms = []
        if cfg.get("all_core"):
            perms = list(all_core_perms)
        else:
            actions = cfg.get("actions", ["view"])
            models = cfg.get("models", [])
            codenames = [f"{a}_{m}" for m in models for a in actions]
            perms = list(Permission.objects.filter(content_type__app_label="core", codename__in=codenames))

        # кастомные права (sql_console / approve_zayavka)
        extra = cfg.get("extra", [])
        if extra:
            perms += list(Permission.objects.filter(content_type__app_label="core", codename__in=extra))

        g.permissions.set(perms)

User = get_user_model()

@receiver(post_save, sender=User)
def ensure_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
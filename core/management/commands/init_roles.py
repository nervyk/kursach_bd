from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

ROLE_PERMS = {
    "Владелец сети": [
        # дать всё по core
        "core.view_tovar", "core.add_tovar", "core.change_tovar", "core.delete_tovar",
        "core.view_postavka", "core.add_postavka", "core.change_postavka", "core.delete_postavka",
        "core.view_vyruchka", "core.add_vyruchka", "core.change_vyruchka", "core.delete_vyruchka",
        "core.view_magazin", "core.add_magazin", "core.change_magazin", "core.delete_magazin",
        "core.view_postavshchik", "core.add_postavshchik", "core.change_postavshchik", "core.delete_postavshchik",
        "core.view_rabotnik", "core.add_rabotnik", "core.change_rabotnik", "core.delete_rabotnik",
        "core.view_gruppatovarov", "core.add_gruppatovarov", "core.change_gruppatovarov", "core.delete_gruppatovarov",
        "core.view_edinitsaizmereniya", "core.add_edinitsaizmereniya", "core.change_edinitsaizmereniya", "core.delete_edinitsaizmereniya",
        "core.view_bank", "core.add_bank", "core.change_bank", "core.delete_bank",
        "core.view_otdel", "core.add_otdel", "core.change_otdel", "core.delete_otdel",
        "core.view_dolzhnost", "core.add_dolzhnost", "core.change_dolzhnost", "core.delete_dolzhnost",
        "core.view_zayavka","core.add_zayavka","core.change_zayavka","core.delete_zayavka",
        "core.view_zayavkaitem","core.add_zayavkaitem","core.change_zayavkaitem","core.delete_zayavkaitem",
        "core.view_magazintovar","core.add_magazintovar","core.change_magazintovar","core.delete_magazintovar",
        "core.approve_zayavka",
        "core.sql_console",

    ],
    "Менеджер по закупкам": [
        "core.view_postavshchik", "core.add_postavshchik", "core.change_postavshchik",
        "core.view_postavka", "core.add_postavka", "core.change_postavka",
        "core.view_tovar", "core.change_tovar",
    ],
    "Директор магазина": [
        "core.view_vyruchka", "core.add_vyruchka", "core.change_vyruchka",
        "core.view_rabotnik",
        "core.view_tovar",
        "core.view_magazin",
        "core.view_zayavka",
        "core.change_zayavka",
        "core.approve_zayavka",
    ],
    "Заведующий складом магазина": [
        "core.view_tovar",
        "core.view_postavka",
    ],
    "Бухгалтер магазина": [
        "core.view_rabotnik", "core.add_rabotnik", "core.change_rabotnik",
    ],
}

class Command(BaseCommand):
    help = "Создать группы ролей и выдать права"

    def handle(self, *args, **kwargs):
        for role, perms in ROLE_PERMS.items():
            g, _ = Group.objects.get_or_create(name=role)
            g.permissions.clear()
            for codename in perms:
                app_label, perm_codename = codename.split(".")
                p = Permission.objects.get(content_type__app_label=app_label, codename=perm_codename)
                g.permissions.add(p)
            self.stdout.write(self.style.SUCCESS(f"OK: {role} ({len(perms)} perms)"))

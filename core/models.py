from django.db import models
from django.db.models import Q
from django.conf import settings
from django.contrib.auth import get_user_model

# ===== Справочники =====

class Strana(models.Model):
    nazvanie = models.CharField(max_length=50)

    class Meta:
        db_table = "strana"

    def __str__(self): return self.nazvanie


class Gorod(models.Model):
    nazvanie = models.CharField(max_length=50)

    class Meta:
        db_table = "gorod"

    def __str__(self): return self.nazvanie


class Ulitsa(models.Model):
    nazvanie = models.CharField(max_length=50)

    class Meta:
        db_table = "ulitsa"

    def __str__(self): return self.nazvanie


class EdinitsaIzmereniya(models.Model):
    nazvanie = models.CharField(max_length=25)

    class Meta:
        db_table = "edinitsa_izmereniya"

    def __str__(self): return self.nazvanie




class Bank(models.Model):
    nazvanie = models.CharField(max_length=50)
    inn = models.CharField(max_length=12, null=True, blank=True)
    bik = models.CharField(max_length=12, null=True, blank=True)
    nomer_korrespondentnogo_scheta = models.CharField(max_length=25, null=True, blank=True)

    class Meta:
        db_table = "bank"

    def __str__(self): return self.nazvanie


class Professiya(models.Model):
    nazvanie = models.CharField(max_length=50)

    class Meta:
        db_table = "professiya"

    def __str__(self): return self.nazvanie


class Specialnost(models.Model):
    nazvanie = models.CharField(max_length=50)

    class Meta:
        db_table = "specialnost"

    def __str__(self): return self.nazvanie


class Klassifikaciya(models.Model):
    nazvanie = models.CharField(max_length=50)

    class Meta:
        db_table = "klassifikaciya"

    def __str__(self): return self.nazvanie


class StruktPodrazdelenie(models.Model):
    nazvanie = models.CharField(max_length=50)

    class Meta:
        db_table = "strukt_podrazdelenie"

    def __str__(self): return self.nazvanie


class Dolzhnost(models.Model):
    nazvanie = models.CharField(max_length=50)

    class Meta:
        db_table = "dolzhnost"

    def __str__(self): return self.nazvanie


class GruppaTovarov(models.Model):
    nazvanie = models.CharField(max_length=25)

    class Meta:
        db_table = "gruppa_tovarov"

    def __str__(self): return self.nazvanie


# ===== Магазины / товары =====

class Magazin(models.Model):
    nazvanie = models.CharField(max_length=50)
    familiya_direktora = models.CharField(max_length=25, null=True, blank=True)
    imya_direktora = models.CharField(max_length=25, null=True, blank=True)
    otchestvo_direktora = models.CharField(max_length=25, null=True, blank=True)

    id_strana = models.ForeignKey(Strana, on_delete=models.PROTECT, null=True, blank=True, db_column="id_strana")
    id_gorod = models.ForeignKey(Gorod, on_delete=models.PROTECT, null=True, blank=True, db_column="id_gorod")
    id_ulica = models.ForeignKey(Ulitsa, on_delete=models.PROTECT, null=True, blank=True, db_column="id_ulica")

    class Meta:
        db_table = "magazin"

    def __str__(self): return self.nazvanie


class Tovar(models.Model):
    id_edinitsa_izmereniya = models.ForeignKey(
        EdinitsaIzmereniya, on_delete=models.PROTECT, null=True, blank=True, db_column="id_edinitsa_izmereniya"
    )
    id_gruppa_tovarov = models.ForeignKey(
        GruppaTovarov, on_delete=models.PROTECT, null=True, blank=True, db_column="id_gruppa_tovarov"
    )

    nazvanie = models.CharField(max_length=25)
    kolichestvo_na_sklade = models.IntegerField(null=True, blank=True)
    cena_postavki = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cena_prodazhi = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "tovar"

    def __str__(self): return self.nazvanie


class MagazinTovar(models.Model):
    id_magazin = models.ForeignKey(Magazin, on_delete=models.PROTECT, db_column="id_magazin")
    id_tovar = models.ForeignKey(Tovar, on_delete=models.PROTECT, db_column="id_tovar")
    kolichestvo = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "magazin_tovar"
        constraints = [
            models.UniqueConstraint(fields=["id_magazin", "id_tovar"], name="uniq_magazin_tovar"),
        ]



# ===== Поставщики / поставки =====

class Postavshchik(models.Model):
    nazvanie = models.CharField(max_length=50)
    kod_po_ok = models.CharField(max_length=20, null=True, blank=True)
    abreviatura = models.CharField(max_length=15, null=True, blank=True)
    nomer_raschetnogo_scheta = models.CharField(max_length=25, null=True, blank=True)

    familiya_rukovoditelya = models.CharField(max_length=25, null=True, blank=True)
    imya_rukovoditelya = models.CharField(max_length=25, null=True, blank=True)
    otchestvo_rukovoditelya = models.CharField(max_length=25, null=True, blank=True)

    nomer_telefona = models.CharField(max_length=25, null=True, blank=True)
    nomer_doma = models.CharField(max_length=25, null=True, blank=True)

    id_bank = models.ForeignKey(Bank, on_delete=models.PROTECT, null=True, blank=True, db_column="id_bank")
    id_strana = models.ForeignKey(Strana, on_delete=models.PROTECT, null=True, blank=True, db_column="id_strana")
    id_gorod = models.ForeignKey(Gorod, on_delete=models.PROTECT, null=True, blank=True, db_column="id_gorod")
    id_ulica = models.ForeignKey(Ulitsa, on_delete=models.PROTECT, null=True, blank=True, db_column="id_ulica")

    class Meta:
        db_table = "postavshchik"

    def __str__(self): return self.nazvanie


class Postavka(models.Model):
    id_postavshchik = models.ForeignKey(Postavshchik, on_delete=models.PROTECT, db_column="id_postavshchik")
    id_tovar = models.ForeignKey(Tovar, on_delete=models.PROTECT, db_column="id_tovar")
    data_postavki = models.DateField(null=True, blank=True)
    kolichestvo = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)

    class Meta:
        db_table = "postavka"


# ===== Выручка =====

class Vyruchka(models.Model):
    id_magazin = models.ForeignKey(
        Magazin, on_delete=models.PROTECT, null=True, blank=True, db_column="id_magazin"
    )
    id_rabotnik = models.ForeignKey(
        "Rabotnik", on_delete=models.PROTECT, null=True, blank=True, db_column="id_rabotnik"
    )
    data = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "vyruchka"


class TovarVyruchka(models.Model):
    id_tovar = models.ForeignKey(Tovar, on_delete=models.PROTECT, db_column="id_tovar")
    id_vyruchka = models.ForeignKey(Vyruchka, on_delete=models.PROTECT, db_column="id_vyruchka")
    kolichestvo = models.IntegerField(null=True, blank=True)

    cena_prodazhi = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    summa = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "tovar_vyruchka"



class Otdel(models.Model):
    id_magazin = models.ForeignKey(
        Magazin, on_delete=models.PROTECT, null=True, blank=True, db_column="id_magazin"
    )
    id_gruppa_tovarov = models.ForeignKey(GruppaTovarov, on_delete=models.PROTECT, db_column="id_gruppa_tovarov")
    nazvanie = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "otdel"


# ===== Персонал =====

class Rabotnik(models.Model):
    class Pol(models.TextChoices):
        MUZH = "Мужской", "Мужской"
        ZHEN = "Женский", "Женский"

    id_strana = models.ForeignKey(Strana, on_delete=models.PROTECT, null=True, blank=True, db_column="id_strana")
    id_gorod = models.ForeignKey(Gorod, on_delete=models.PROTECT, null=True, blank=True, db_column="id_gorod")
    id_ulica = models.ForeignKey(Ulitsa, on_delete=models.PROTECT, null=True, blank=True, db_column="id_ulica")
    id_dolzhnost = models.ForeignKey(Dolzhnost, on_delete=models.PROTECT, null=True, blank=True, db_column="id_dolzhnost")

    familiya = models.CharField(max_length=25, null=True, blank=True)
    imya = models.CharField(max_length=25, null=True, blank=True)
    otchestvo = models.CharField(max_length=25, null=True, blank=True)

    data_rozhdeniya = models.DateField(null=True, blank=True)
    nomer_doma = models.CharField(max_length=5, null=True, blank=True)
    trudovoy_stazh = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    pol = models.CharField(max_length=10, choices=Pol.choices, null=True, blank=True)
    id_otdela = models.ForeignKey(Otdel, on_delete=models.PROTECT, null=True, blank=True, db_column="id_otdela")

    class Meta:
        db_table = "rabotnik"
        constraints = [
            models.CheckConstraint(
                condition=Q(pol__in=["Мужской", "Женский"]) | Q(pol__isnull=True),
                name="rabotnik_pol_check",
            )

        ]

    def __str__(self):
        return " ".join(x for x in [self.familiya, self.imya, self.otchestvo] if x) or f"Rabotnik {self.pk}"


class RabotnikVyruchka(models.Model):
    id_rabotnik = models.ForeignKey(Rabotnik, on_delete=models.PROTECT, db_column="id_rabotnik")
    id_vyruchka = models.ForeignKey(Vyruchka, on_delete=models.PROTECT, db_column="id_vyruchka")

    class Meta:
        db_table = "rabotnik_vyruchka"


class MestoRaboty(models.Model):
    id_strana = models.ForeignKey(Strana, on_delete=models.PROTECT, null=True, blank=True, db_column="id_strana")
    id_gorod = models.ForeignKey(Gorod, on_delete=models.PROTECT, null=True, blank=True, db_column="id_gorod")
    id_ulica = models.ForeignKey(Ulitsa, on_delete=models.PROTECT, null=True, blank=True, db_column="id_ulica")
    nazvanie = models.CharField(max_length=50, null=True, blank=True)
    nomer_doma = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        db_table = "mesto_raboty"

    def __str__(self): return self.nazvanie or f"MestoRaboty {self.pk}"


class ZapisiTrudKnizhke(models.Model):
    class VidDokumenta(models.TextChoices):
        PRIEM = "Прием", "Прием"
        UVOL = "Увольнение", "Увольнение"
        PEREVOD = "Перевод", "Перевод"

    id_rabotnika = models.ForeignKey(Rabotnik, on_delete=models.PROTECT, db_column="id_rabotnika")
    id_mesto_raboty = models.ForeignKey(MestoRaboty, on_delete=models.PROTECT, db_column="id_mesto_raboty")
    id_strukturnoe_podrazdelenie = models.ForeignKey(StruktPodrazdelenie, on_delete=models.PROTECT, db_column="id_strukturnoe_podrazdelenie")
    id_professii = models.ForeignKey(Professiya, on_delete=models.PROTECT, db_column="id_professii")
    id_specialnosti = models.ForeignKey(Specialnost, on_delete=models.PROTECT, db_column="id_specialnosti")
    id_klassifikacii = models.ForeignKey(Klassifikaciya, on_delete=models.PROTECT, db_column="id_klassifikacii")
    id_dolzhnosti = models.ForeignKey(Dolzhnost, on_delete=models.PROTECT, db_column="id_dolzhnosti")

    data_priema_na_rabotu = models.DateField(null=True, blank=True)
    data_uvolenija = models.DateField(null=True, blank=True)
    vid_meropriyatiya = models.CharField(max_length=50, null=True, blank=True)
    data = models.DateField(null=True, blank=True)
    prichina_prekrashcheniya_tr = models.TextField(null=True, blank=True)
    nomer = models.CharField(max_length=10, null=True, blank=True)
    vid_dokumenta = models.CharField(max_length=10, choices=VidDokumenta.choices, null=True, blank=True)

    class Meta:
        db_table = "zapisi_trud_knizhke"
        constraints = [
            models.CheckConstraint(
                condition=Q(vid_dokumenta__in=["Прием", "Увольнение", "Перевод"]) | Q(vid_dokumenta__isnull=True),
                name="zapisi_vid_dokumenta_check",
            )

        ]

class Zayavka(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Черновик"
        SENT = "SENT", "Отправлена"
        APPROVED = "APPROVED", "Одобрена"
        REJECTED = "REJECTED", "Отклонена"

    id_magazin = models.ForeignKey(Magazin, on_delete=models.PROTECT, db_column="id_magazin")
    data_zayavki = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    comment = models.TextField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="zayavki_created"
    )

    class Meta:
        db_table = "zayavka"
        permissions = [
            ("approve_zayavka", "Может проводить (одобрять) заявки"),
            ("sql_console", "Доступ к SQL-консоли"),
        ]

    def __str__(self):
        return f"Заявка #{self.pk} ({self.get_status_display()})"


class ZayavkaItem(models.Model):
    id_zayavka = models.ForeignKey(Zayavka, on_delete=models.CASCADE, db_column="id_zayavka")
    id_tovar = models.ForeignKey(Tovar, on_delete=models.PROTECT, db_column="id_tovar")
    kolichestvo = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "zayavka_item"
        constraints = [
            models.UniqueConstraint(fields=["id_zayavka", "id_tovar"], name="uniq_zayavka_item"),
        ]


User = get_user_model()

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    id_magazin = models.ForeignKey("Magazin", on_delete=models.PROTECT, null=True, blank=True, db_column="id_magazin")
    id_otdel = models.ForeignKey("Otdel", on_delete=models.PROTECT, null=True, blank=True, db_column="id_otdel")

    class Meta:
        db_table = "user_profile"
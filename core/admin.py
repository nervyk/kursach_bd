from django.contrib import admin
from . import models

admin.site.register([
    models.Strana, models.Gorod, models.Ulitsa,
    models.EdinitsaIzmereniya, models.Bank,
    models.Professiya, models.Specialnost, models.Klassifikaciya, models.StruktPodrazdelenie,
    models.Dolzhnost, models.GruppaTovarov,
    models.Magazin, models.Tovar, models.MagazinTovar,
    models.Postavshchik, models.Postavka,
    models.Vyruchka, models.TovarVyruchka,
    models.Otdel, models.Rabotnik, models.RabotnikVyruchka,
    models.MestoRaboty, models.ZapisiTrudKnizhke,
])

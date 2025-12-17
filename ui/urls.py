from django.urls import path
from . import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),

    # ===== Товары =====
    path("tovar/", views.TovarListView.as_view(), name="tovar_list"),
    path("tovar/add/", views.TovarCreateView.as_view(), name="tovar_add"),
    path("tovar/<int:pk>/edit/", views.TovarUpdateView.as_view(), name="tovar_edit"),
    path("tovar/<int:pk>/delete/", views.TovarDeleteView.as_view(), name="tovar_delete"),

    # ===== Поставки =====
    path("postavka/", views.PostavkaListView.as_view(), name="postavka_list"),
    path("postavka/add/", views.PostavkaCreateView.as_view(), name="postavka_add"),
    path("postavka/<int:pk>/edit/", views.PostavkaUpdateView.as_view(), name="postavka_edit"),
    path("postavka/<int:pk>/delete/", views.PostavkaDeleteView.as_view(), name="postavka_delete"),

    # ===== Выручка =====
    path("vyruchka/", views.VyruchkaListView.as_view(), name="vyruchka_list"),
    path("vyruchka/add/", views.VyruchkaCreateView.as_view(), name="vyruchka_add"),
    path("vyruchka/<int:pk>/edit/", views.VyruchkaUpdateView.as_view(), name="vyruchka_edit"),
    path("vyruchka/<int:pk>/delete/", views.VyruchkaDeleteView.as_view(), name="vyruchka_delete"),

    # ===== Справочники =====
    path("spravochnik/gruppa-tovarov/", views.GruppaTovarovListView.as_view(), name="gruppa_list"),
    path("spravochnik/gruppa-tovarov/add/", views.GruppaTovarovCreateView.as_view(), name="gruppa_add"),
    path("spravochnik/gruppa-tovarov/<int:pk>/edit/", views.GruppaTovarovUpdateView.as_view(), name="gruppa_edit"),
    path("spravochnik/gruppa-tovarov/<int:pk>/delete/", views.GruppaTovarovDeleteView.as_view(), name="gruppa_delete"),

    path("spravochnik/edinitsa-izmereniya/", views.EdinitsaIzmereniyaListView.as_view(), name="edinitsa_list"),
    path("spravochnik/edinitsa-izmereniya/add/", views.EdinitsaIzmereniyaCreateView.as_view(), name="edinitsa_add"),
    path("spravochnik/edinitsa-izmereniya/<int:pk>/edit/", views.EdinitsaIzmereniyaUpdateView.as_view(), name="edinitsa_edit"),
    path("spravochnik/edinitsa-izmereniya/<int:pk>/delete/", views.EdinitsaIzmereniyaDeleteView.as_view(), name="edinitsa_delete"),

    path("spravochnik/bank/", views.BankListView.as_view(), name="bank_list"),
    path("spravochnik/bank/add/", views.BankCreateView.as_view(), name="bank_add"),
    path("spravochnik/bank/<int:pk>/edit/", views.BankUpdateView.as_view(), name="bank_edit"),
    path("spravochnik/bank/<int:pk>/delete/", views.BankDeleteView.as_view(), name="bank_delete"),

    path("spravochnik/dolzhnost/", views.DolzhnostListView.as_view(), name="dolzhnost_list"),
    path("spravochnik/dolzhnost/add/", views.DolzhnostCreateView.as_view(), name="dolzhnost_add"),
    path("spravochnik/dolzhnost/<int:pk>/edit/", views.DolzhnostUpdateView.as_view(), name="dolzhnost_edit"),
    path("spravochnik/dolzhnost/<int:pk>/delete/", views.DolzhnostDeleteView.as_view(), name="dolzhnost_delete"),

    path("spravochnik/otdel/", views.OtdelListView.as_view(), name="otdel_list"),
    path("spravochnik/otdel/add/", views.OtdelCreateView.as_view(), name="otdel_add"),
    path("spravochnik/otdel/<int:pk>/edit/", views.OtdelUpdateView.as_view(), name="otdel_edit"),
    path("spravochnik/otdel/<int:pk>/delete/", views.OtdelDeleteView.as_view(), name="otdel_delete"),
    path("spravochnik/", views.SpravochnikHomeView.as_view(), name="spravochnik_home"),
    path("spravochnik/strana/", views.StranaListView.as_view(), name="strana_list"),

    path("spravochnik/strana/add/", views.StranaCreateView.as_view(), name="strana_add"),
    path("spravochnik/strana/<int:pk>/edit/", views.StranaUpdateView.as_view(), name="strana_edit"),
    path("spravochnik/strana/<int:pk>/delete/", views.StranaDeleteView.as_view(), name="strana_delete"),

    path("spravochnik/gorod/", views.GorodListView.as_view(), name="gorod_list"),
    path("spravochnik/gorod/add/", views.GorodCreateView.as_view(), name="gorod_add"),
    path("spravochnik/gorod/<int:pk>/edit/", views.GorodUpdateView.as_view(), name="gorod_edit"),
    path("spravochnik/gorod/<int:pk>/delete/", views.GorodDeleteView.as_view(), name="gorod_delete"),

    path("spravochnik/ulitsa/", views.UlitsaListView.as_view(), name="ulitsa_list"),
    path("spravochnik/ulitsa/add/", views.UlitsaCreateView.as_view(), name="ulitsa_add"),
    path("spravochnik/ulitsa/<int:pk>/edit/", views.UlitsaUpdateView.as_view(), name="ulitsa_edit"),
    path("spravochnik/ulitsa/<int:pk>/delete/", views.UlitsaDeleteView.as_view(), name="ulitsa_delete"),

    # ===== Кадровые справочники =====
    path("spravochnik/professiya/", views.ProfessiyaListView.as_view(), name="professiya_list"),
    path("spravochnik/professiya/add/", views.ProfessiyaCreateView.as_view(), name="professiya_add"),
    path("spravochnik/professiya/<int:pk>/edit/", views.ProfessiyaUpdateView.as_view(), name="professiya_edit"),
    path("spravochnik/professiya/<int:pk>/delete/", views.ProfessiyaDeleteView.as_view(), name="professiya_delete"),

    path("spravochnik/specialnost/", views.SpecialnostListView.as_view(), name="specialnost_list"),
    path("spravochnik/specialnost/add/", views.SpecialnostCreateView.as_view(), name="specialnost_add"),
    path("spravochnik/specialnost/<int:pk>/edit/", views.SpecialnostUpdateView.as_view(), name="specialnost_edit"),
    path("spravochnik/specialnost/<int:pk>/delete/", views.SpecialnostDeleteView.as_view(), name="specialnost_delete"),

    path("spravochnik/klassifikaciya/", views.KlassifikaciyaListView.as_view(), name="klassifikaciya_list"),
    path("spravochnik/klassifikaciya/add/", views.KlassifikaciyaCreateView.as_view(), name="klassifikaciya_add"),
    path("spravochnik/klassifikaciya/<int:pk>/edit/", views.KlassifikaciyaUpdateView.as_view(), name="klassifikaciya_edit"),
    path("spravochnik/klassifikaciya/<int:pk>/delete/", views.KlassifikaciyaDeleteView.as_view(), name="klassifikaciya_delete"),

    path("spravochnik/strukt-podrazdelenie/", views.StruktPodrazdelenieListView.as_view(), name="strukt_list"),
    path("spravochnik/strukt-podrazdelenie/add/", views.StruktPodrazdelenieCreateView.as_view(), name="strukt_add"),
    path("spravochnik/strukt-podrazdelenie/<int:pk>/edit/", views.StruktPodrazdelenieUpdateView.as_view(), name="strukt_edit"),
    path("spravochnik/strukt-podrazdelenie/<int:pk>/delete/", views.StruktPodrazdelenieDeleteView.as_view(), name="strukt_delete"),

    # ===== Кадровые документы =====
    path("kadry/mesto-raboty/", views.MestoRabotyListView.as_view(), name="mestoraboty_list"),
    path("kadry/mesto-raboty/add/", views.MestoRabotyCreateView.as_view(), name="mestoraboty_add"),
    path("kadry/mesto-raboty/<int:pk>/edit/", views.MestoRabotyUpdateView.as_view(), name="mestoraboty_edit"),
    path("kadry/mesto-raboty/<int:pk>/delete/", views.MestoRabotyDeleteView.as_view(), name="mestoraboty_delete"),

    path("kadry/trud-knizhka/", views.ZapisiTrudKnizhkeListView.as_view(), name="trud_list"),
    path("kadry/trud-knizhka/add/", views.ZapisiTrudKnizhkeCreateView.as_view(), name="trud_add"),
    path("kadry/trud-knizhka/<int:pk>/edit/", views.ZapisiTrudKnizhkeUpdateView.as_view(), name="trud_edit"),
    path("kadry/trud-knizhka/<int:pk>/delete/", views.ZapisiTrudKnizhkeDeleteView.as_view(), name="trud_delete"),


    # ===== Магазины =====
    path("magazin/", views.MagazinListView.as_view(), name="magazin_list"),
    path("magazin/add/", views.MagazinCreateView.as_view(), name="magazin_add"),
    path("magazin/<int:pk>/edit/", views.MagazinUpdateView.as_view(), name="magazin_edit"),
    path("magazin/<int:pk>/delete/", views.MagazinDeleteView.as_view(), name="magazin_delete"),

    # ===== Поставщики =====
    path("postavshchik/", views.PostavshchikListView.as_view(), name="postavshchik_list"),
    path("postavshchik/add/", views.PostavshchikCreateView.as_view(), name="postavshchik_add"),
    path("postavshchik/<int:pk>/edit/", views.PostavshchikUpdateView.as_view(), name="postavshchik_edit"),
    path("postavshchik/<int:pk>/delete/", views.PostavshchikDeleteView.as_view(), name="postavshchik_delete"),
    path("zayavka/", views.ZayavkaListView.as_view(), name="zayavka_list"),
    path("zayavka/add/", views.ZayavkaCreateView.as_view(), name="zayavka_add"),
    path("zayavka/<int:pk>/edit/", views.ZayavkaUpdateView.as_view(), name="zayavka_edit"),
    path("zayavka/<int:pk>/approve/", views.ZayavkaApproveView.as_view(), name="zayavka_approve"),

    # ===== Работники =====
    path("rabotnik/", views.RabotnikListView.as_view(), name="rabotnik_list"),
    path("rabotnik/add/", views.RabotnikCreateView.as_view(), name="rabotnik_add"),
    path("rabotnik/<int:pk>/edit/", views.RabotnikUpdateView.as_view(), name="rabotnik_edit"),
    path("rabotnik/<int:pk>/delete/", views.RabotnikDeleteView.as_view(), name="rabotnik_delete"),
    path("analytics/", views.AnalyticsView.as_view(), name="analytics"),
    path("analytics/export.csv", views.analytics_export_csv, name="analytics_export_csv"),
    path("sql/", views.SqlConsoleView.as_view(), name="sql_console"),
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("users/add/", views.UserCreateView.as_view(), name="user_add"),
    path("users/<int:pk>/edit/", views.UserUpdateView.as_view(), name="user_edit"),
    path("users/<int:pk>/delete/", views.UserDeleteView.as_view(), name="user_delete"),
    path("zayavka/<int:pk>/send/", views.ZayavkaSendView.as_view(), name="zayavka_send"),
    path("zayavka/<int:pk>/delete/", views.ZayavkaDeleteView.as_view(), name="zayavka_delete"),
    path("sklad-magazina/", views.MagazinTovarListView.as_view(), name="magazintovar_list"),
    

    path("help/user-guide/", views.UserGuideView.as_view(), name="help_user_guide"),
    path("help/about/", views.AboutView.as_view(), name="help_about"),
    path("settings/", views.SettingsView.as_view(), name="settings"),

    
]
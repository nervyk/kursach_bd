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
    path("analytics/export.xlsx", views.analytics_export_xlsx, name="analytics_export_xlsx"),
    path("analytics/export.pdf", views.analytics_export_pdf, name="analytics_export_pdf"),
    path("zayavka/<int:pk>/send/", views.ZayavkaSendView.as_view(), name="zayavka_send"),
    path("zayavka/<int:pk>/delete/", views.ZayavkaDeleteView.as_view(), name="zayavka_delete"),
    path("sklad-magazina/", views.MagazinTovarListView.as_view(), name="magazintovar_list"),

]
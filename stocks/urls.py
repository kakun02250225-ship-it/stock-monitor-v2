from django.urls import path

from . import views

# app_name を付けると、テンプレートで "stocks:list" のように
# 名前空間つきでURLを参照できる（他アプリと名前が衝突しない）。
app_name = "stocks"

urlpatterns = [
    path("", views.StockListView.as_view(), name="list"),
    path("add/", views.StockCreateView.as_view(), name="add"),
    path("<int:pk>/edit/", views.StockUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.StockDeleteView.as_view(), name="delete"),
    # フェーズ3: 評価レポートの JSON API
    path("api/report/", views.report_api, name="report_api"),
    path("api/report/all/", views.report_all_api, name="report_all_api"),
]

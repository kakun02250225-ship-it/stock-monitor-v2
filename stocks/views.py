from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .models import Stock
from .forms import StockForm


# Django には CRUD の定番処理をまとめた「汎用クラスビュー」がある。
# これらを継承すると、一覧・追加・編集・削除を少ないコードで書ける。


class StockListView(ListView):
    """一覧表示（Read）。保有している全銘柄を表示する。"""

    model = Stock
    template_name = "stocks/stock_list.html"
    context_object_name = "stocks"  # テンプレート側で {{ stocks }} として使える


class StockCreateView(CreateView):
    """新規追加（Create）。フォームを表示し、送信されたら保存する。"""

    model = Stock
    form_class = StockForm
    template_name = "stocks/stock_form.html"
    # 保存に成功したら一覧ページへ戻る
    success_url = reverse_lazy("stocks:list")


class StockUpdateView(UpdateView):
    """編集（Update）。既存銘柄をフォームに入れて表示し、更新する。"""

    model = Stock
    form_class = StockForm
    template_name = "stocks/stock_form.html"
    success_url = reverse_lazy("stocks:list")


class StockDeleteView(DeleteView):
    """削除（Delete）。確認ページを出し、OKなら削除する。"""

    model = Stock
    template_name = "stocks/stock_confirm_delete.html"
    success_url = reverse_lazy("stocks:list")

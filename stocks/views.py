from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .models import Stock
from .forms import StockForm


# LoginRequiredMixin を継承すると「ログインしていないと使えない」ビューになる。
# 未ログインなら自動でログインページへ飛ばされる。
# さらに get_queryset で「自分の銘柄だけ」に絞ることで、他人のデータを守る。


class StockListView(LoginRequiredMixin, ListView):
    """一覧表示（Read）。ログイン中ユーザー自身の銘柄だけを表示する。"""

    model = Stock
    template_name = "stocks/stock_list.html"
    context_object_name = "stocks"

    def get_queryset(self):
        # 全銘柄ではなく、持ち主が自分のものだけに絞る
        return Stock.objects.filter(owner=self.request.user)


class StockCreateView(LoginRequiredMixin, CreateView):
    """新規追加（Create）。保存時に持ち主を「自分」に設定する。"""

    model = Stock
    form_class = StockForm
    template_name = "stocks/stock_form.html"
    success_url = reverse_lazy("stocks:list")

    def form_valid(self, form):
        # フォームに owner 欄は無いので、保存直前にログイン中ユーザーを持ち主にする
        form.instance.owner = self.request.user
        return super().form_valid(form)


class StockUpdateView(LoginRequiredMixin, UpdateView):
    """編集（Update）。自分の銘柄だけ編集できる。"""

    model = Stock
    form_class = StockForm
    template_name = "stocks/stock_form.html"
    success_url = reverse_lazy("stocks:list")

    def get_queryset(self):
        # 他人の銘柄IDをURLに打ち込んでも編集できないよう、対象を自分の銘柄に限定する
        return Stock.objects.filter(owner=self.request.user)


class StockDeleteView(LoginRequiredMixin, DeleteView):
    """削除（Delete）。自分の銘柄だけ削除できる。"""

    model = Stock
    template_name = "stocks/stock_confirm_delete.html"
    success_url = reverse_lazy("stocks:list")

    def get_queryset(self):
        # 編集と同様、他人の銘柄を削除できないよう自分の銘柄に限定する
        return Stock.objects.filter(owner=self.request.user)

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .models import Stock
from .forms import StockForm
from .services import build_report


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


# ====== フェーズ3: JSON API（株価取得＋評価レポート） ======
# 日本語をそのまま読めるよう ensure_ascii=False、見やすいよう indent=2 にする。
_JSON_OPTS = {"json_dumps_params": {"ensure_ascii": False, "indent": 2}}


@login_required
def report_api(request):
    """ログイン中ユーザー自身の評価レポートを JSON で返す。

    ブラウザでログインした状態で /api/report/ を開くと、自分の保有銘柄の
    現在価格・評価額・損益・売買判定が見られる（動作確認用）。
    """
    return JsonResponse(build_report(request.user), **_JSON_OPTS)


def report_all_api(request):
    """全ユーザーの評価レポートを JSON で返す（GitHub Actions のメール送信用）。

    財務情報なので、環境変数 REPORT_API_TOKEN と一致する token が無いと拒否する。
    GitHub Actions は ?token=... を付けてこのURLを叩き、結果を各ユーザーへメールする。
    """
    token = request.GET.get("token", "")
    expected = settings.REPORT_API_TOKEN
    # トークン未設定 or 不一致なら拒否（空文字での素通りを防ぐ）
    if not expected or token != expected:
        return HttpResponseForbidden("invalid token")

    User = get_user_model()
    reports = [
        build_report(user)
        for user in User.objects.all()
        if user.stocks.exists()  # 銘柄を持つユーザーだけ
    ]
    return JsonResponse({"reports": reports}, **_JSON_OPTS)

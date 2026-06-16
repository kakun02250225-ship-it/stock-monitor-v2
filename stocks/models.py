from django.conf import settings
from django.db import models


class Stock(models.Model):
    """保有している1銘柄を表すモデル。

    フェーズ2でマルチユーザー化。owner（持ち主）を必須にし、
    各ユーザーは自分の owner の銘柄だけを操作できる。
    """

    # 市場区分の選択肢。DBには "jp" / "us" が入り、画面には日本語ラベルを出す。
    MARKET_CHOICES = [
        ("jp", "日本株"),
        ("us", "米国株"),
    ]

    # 持ち主。Django標準のユーザーと1対多で紐づける。
    # ユーザーが削除されたら、その人の銘柄もまとめて削除する（CASCADE）。
    # related_name="stocks" で user.stocks.all() のように逆引きできる。
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="stocks",
        verbose_name="持ち主",
    )

    name = models.CharField("会社名", max_length=100)
    ticker = models.CharField("ティッカー", max_length=20)
    market = models.CharField("市場区分", max_length=2, choices=MARKET_CHOICES)

    # PayPay証券は金額指定で買えるため株数は小数になる（例: 1.0035545904）。
    # 桁あふれしないよう小数10桁まで保持する。
    shares = models.DecimalField("保有株数", max_digits=20, decimal_places=10)

    # 投資元本（円）。日本株も米国株も PayPay では円で投資するため、共通で円で持つ。
    # 評価額は、日本株はそのまま円、米国株は現在価格(ドル)を為替で円換算して求める。
    cost = models.PositiveIntegerField("投資元本（円）", null=True, blank=True)

    # 作成日時・更新日時（一覧の並び順や確認用）
    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    class Meta:
        ordering = ["-created_at"]  # 新しく追加した銘柄を上に表示

    def __str__(self):
        # 管理画面やデバッグで分かりやすいよう「会社名（ティッカー）」を返す
        return f"{self.name}（{self.ticker}）"

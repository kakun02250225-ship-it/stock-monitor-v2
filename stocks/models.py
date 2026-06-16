from django.db import models


class Stock(models.Model):
    """保有している1銘柄を表すモデル。

    フェーズ1（自分1人用）では owner は持たない。
    マルチユーザー化（フェーズ2）で owner フィールドを追加する。
    """

    # 市場区分の選択肢。DBには "jp" / "us" が入り、画面には日本語ラベルを出す。
    MARKET_CHOICES = [
        ("jp", "日本株"),
        ("us", "米国株"),
    ]

    name = models.CharField("会社名", max_length=100)
    ticker = models.CharField("ティッカー", max_length=20)
    market = models.CharField("市場区分", max_length=2, choices=MARKET_CHOICES)

    # PayPay証券は金額指定で買えるため株数は小数になる（例: 1.0035545904）。
    # 桁あふれしないよう小数10桁まで保持する。
    shares = models.DecimalField("保有株数", max_digits=20, decimal_places=10)

    # 日本株は投資元本（円）で損益を計算する。米国株では使わないので任意。
    cost = models.PositiveIntegerField("投資元本（円）", null=True, blank=True)

    # 米国株（SOXLなど）は取得単価ベースで持つケース用。日本株では使わないので任意。
    buy_price = models.PositiveIntegerField("買付額", null=True, blank=True)

    # 作成日時・更新日時（一覧の並び順や確認用）
    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    class Meta:
        ordering = ["-created_at"]  # 新しく追加した銘柄を上に表示

    def __str__(self):
        # 管理画面やデバッグで分かりやすいよう「会社名（ティッカー）」を返す
        return f"{self.name}（{self.ticker}）"

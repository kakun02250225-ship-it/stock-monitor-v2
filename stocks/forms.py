from django import forms

from .models import Stock


class StockForm(forms.ModelForm):
    """銘柄の追加・編集に使うフォーム。

    ModelForm を使うと、モデルの定義からフォームの入力欄を自動生成できる。
    自分でHTMLの<input>を1つずつ書く必要がない。
    """

    class Meta:
        model = Stock
        # ユーザーが入力する項目だけを並べる（created_at などは自動なので除外）
        fields = ["name", "ticker", "market", "shares", "cost", "buy_price"]

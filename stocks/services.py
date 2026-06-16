"""株価の取得と、評価額・損益・売買判定の計算をまとめたモジュール。

ここに「外部(yfinance)から株価を取る処理」と「お金の計算ロジック」を集約する。
ビューやAPIはこの関数を呼ぶだけにして、計算の置き場所を1か所にする
（テストしやすく、後で式を直すときもここだけ見ればよい）。
"""

from decimal import Decimal, ROUND_HALF_UP

import yfinance as yf


# ---- 売買判定のしきい値（必要に応じて調整する） ----
TAKE_PROFIT_PCT = Decimal("20")   # +20%以上で「利確検討」
CUT_LOSS_PCT = Decimal("-10")     # -10%以下で「損切り検討」


def fetch_price(ticker: str) -> Decimal | None:
    """yfinance で最新の終値を取得する。取れなければ None を返す。

    日本株は "7974.T"、米国株は "SOXL" のようなティッカーを渡す。
    """
    data = yf.Ticker(ticker).history(period="1d")
    if data.empty:
        return None
    return Decimal(str(data["Close"].iloc[-1]))


def fetch_usdjpy() -> Decimal | None:
    """USD/JPY の為替レートを取得する（米国株を円換算するため）。"""
    return fetch_price("JPY=X")


def judge(return_pct: Decimal) -> str:
    """リターン%から売買判定の文言を返す。"""
    if return_pct >= TAKE_PROFIT_PCT:
        return "利確検討"
    if return_pct <= CUT_LOSS_PCT:
        return "損切り検討"
    return "ホールド"


def _yen(value: Decimal) -> int:
    """円は整数に丸める（四捨五入）。"""
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def evaluate(stock, price: Decimal, usdjpy: Decimal | None) -> dict:
    """1銘柄の評価額・損益・リターン%・判定を「円建て」で計算して返す。

    - 日本株: 価格は円。評価額 = price × shares、元本 = cost
    - 米国株: 価格はドル。評価額 = price × shares × USD/JPY、元本 = buy_price（円）
      ※ 米国株も円に換算して日本株と見方を揃える（円建て統一）
    """
    shares = stock.shares

    if stock.market == "us":
        # 米国株はドル建て。価格も元本(buy_price)も同じドル建てなので、
        # 評価額・元本の両方を為替で円に換算する（片方だけ換算すると%が壊れる）。
        rate = usdjpy if usdjpy is not None else Decimal("0")
        value = price * shares * rate
        cost = Decimal(stock.buy_price or 0) * rate
    else:
        # 日本株はそのまま円
        value = price * shares
        cost = Decimal(stock.cost or 0)

    profit = value - cost
    # 元本が0だと割り算できないので、その場合はリターン0%扱いにする
    return_pct = (profit / cost * Decimal("100")) if cost else Decimal("0")

    return {
        "value": _yen(value),                                   # 評価額（円）
        "cost": _yen(cost),                                     # 元本（円）
        "profit": _yen(profit),                                 # 損益（円）
        "return_pct": float(return_pct.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        "judgment": judge(return_pct),                          # 売買判定
    }


def build_report(user) -> dict:
    """指定ユーザーの全銘柄について、現在の評価レポートを組み立てて返す。

    返り値は JSON にしてそのまま API で返せる形（辞書）。
    """
    usdjpy = fetch_usdjpy()
    items = []
    total_value = 0
    total_cost = 0

    for stock in user.stocks.all():
        price = fetch_price(stock.ticker)
        if price is None:
            # 株価が取れなかった銘柄はエラー印をつけてスキップ
            items.append({
                "name": stock.name,
                "ticker": stock.ticker,
                "error": "株価を取得できませんでした",
            })
            continue

        ev = evaluate(stock, price, usdjpy)
        total_value += ev["value"]
        total_cost += ev["cost"]
        items.append({
            "name": stock.name,
            "ticker": stock.ticker,
            "market": stock.get_market_display(),
            "shares": float(stock.shares),
            "price": float(price),
            **ev,
        })

    total_profit = total_value - total_cost
    return {
        "username": user.username,
        "email": user.email,
        "usdjpy": float(usdjpy) if usdjpy is not None else None,
        "items": items,
        "total": {
            "value": total_value,
            "cost": total_cost,
            "profit": total_profit,
            "return_pct": round(total_profit / total_cost * 100, 2) if total_cost else 0,
        },
    }

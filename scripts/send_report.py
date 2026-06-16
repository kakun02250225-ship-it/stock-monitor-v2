"""毎朝の評価レポートメールを送るスクリプト（GitHub Actions から実行）。

役割分担:
- Django 側の API (/api/report/all/) が「全ユーザーの評価レポート」を JSON で返す
- このスクリプトがその JSON を読み、ユーザーごとに各自のメールアドレスへ送る

標準ライブラリだけで動く（GitHub Actions で余計な pip install が要らない）。

必要な環境変数:
- REPORT_API_URL : 全ユーザーレポートAPIのURL（例: https://<デプロイ先>/api/report/all/）
- REPORT_API_TOKEN : APIを叩くための合言葉（Django側の設定と一致させる）
- MAIL_USERNAME, MAIL_PASSWORD : 送信元Gmailとアプリパスワード
- MAIL_HOST (任意, 既定 smtp.gmail.com), MAIL_PORT (任意, 既定 465)

MAIL_USERNAME / MAIL_PASSWORD が未設定なら「ドライラン」になり、
実際には送らずメール内容を画面に表示する（ローカル確認用）。
"""

import os
import smtplib
import ssl
import sys
from email.mime.text import MIMEText
from urllib.parse import urlencode
from urllib.request import urlopen
import json


def fetch_reports() -> list[dict]:
    """Django API から全ユーザーのレポートを取得する。"""
    base = os.environ["REPORT_API_URL"]
    token = os.environ.get("REPORT_API_TOKEN", "")
    url = f"{base}?{urlencode({'token': token})}"
    with urlopen(url, timeout=60) as res:
        data = json.loads(res.read().decode("utf-8"))
    return data["reports"]


def build_body(report: dict) -> str:
    """1ユーザー分のレポートをメール本文（テキスト）に整形する。"""
    lines = [f"{report['username']} さんの保有銘柄レポート", ""]
    if report.get("usdjpy"):
        lines.append(f"USD/JPY: {report['usdjpy']}")
        lines.append("")

    for item in report["items"]:
        if "error" in item:
            lines.append(f"・{item['name']}（{item['ticker']}）: {item['error']}")
            continue
        lines.append(
            f"・{item['name']}（{item['ticker']} / {item['market']}）"
        )
        lines.append(
            f"    現在値 {item['price']} / 評価額 {item['value']:,}円 / "
            f"損益 {item['profit']:+,}円（{item['return_pct']:+.2f}%）→ {item['judgment']}"
        )

    total = report["total"]
    lines.append("")
    lines.append(
        f"【合計】評価額 {total['value']:,}円 / "
        f"損益 {total['profit']:+,}円（{total['return_pct']:+.2f}%）"
    )
    return "\n".join(lines)


def send_email(to_addr: str, subject: str, body: str) -> None:
    """1通のメールを送る。認証情報が無ければドライラン（表示のみ）。"""
    user = os.environ.get("MAIL_USERNAME")
    password = os.environ.get("MAIL_PASSWORD")

    if not user or not password:
        # ドライラン: 送らずに内容を表示する
        print("=" * 50)
        print(f"[ドライラン] To: {to_addr}")
        print(f"Subject: {subject}")
        print(body)
        print("=" * 50)
        return

    host = os.environ.get("MAIL_HOST", "smtp.gmail.com")
    port = int(os.environ.get("MAIL_PORT", "465"))

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_addr

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(host, port, context=context) as server:
        server.login(user, password)
        server.send_message(msg)
    print(f"送信完了: {to_addr}")


def main() -> int:
    reports = fetch_reports()
    if not reports:
        print("対象ユーザーがいません。")
        return 0

    for report in reports:
        to_addr = report.get("email")
        if not to_addr:
            print(f"メールアドレス未登録のためスキップ: {report['username']}")
            continue
        body = build_body(report)
        send_email(to_addr, "【株価モニター】本日の保有銘柄レポート", body)
    return 0


if __name__ == "__main__":
    sys.exit(main())

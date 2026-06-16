# stock-monitor-v2

PayPay証券で保有している銘柄を Web 上で管理し、毎朝その評価額・損益・売買判定をメールで受け取るためのアプリ。

詳しい背景・設計は `PROJECT.md`（引き継ぎ書）を参照。

## 開発フェーズ

- [x] **フェーズ1**: 自分1人用の CRUD（銘柄の追加・表示・編集・削除）
- [x] **フェーズ2**: ログイン認証 + ユーザーごとのデータ分離
- [x] **フェーズ3**: 株価取得（yfinance）とメール送信（GitHub Actions 連携）  ← イマココ
- [ ] フェーズ4: デプロイ（Fly.io / PostgreSQL）

## 技術スタック

- バックエンド: Django 5.2
- DB: SQLite（開発）→ PostgreSQL（デプロイ時）
- 株価取得: yfinance（フェーズ3で導入）

## ローカルでの動かし方

```bash
# 1. 依存をインストール
pip install -r requirements.txt

# 2. DBを用意（マイグレーション）
python manage.py migrate

# 3. ログイン用のユーザーを作る（最初に作った人が初期データの持ち主＝ID 1 になる）
python manage.py createsuperuser

# 4. 初期データ（v1から引き継いだ3銘柄）を入れる ※任意
#    手順3で作ったユーザー(ID 1)の銘柄として登録される
python manage.py loaddata initial_stocks

# 5. 開発サーバーを起動
python manage.py runserver
```

起動後、ブラウザで http://127.0.0.1:8000/ を開く。未ログインなら
ログインページに飛ぶので、手順3で作ったユーザーでログインすると、
自分の保有銘柄一覧が表示される。

> フェーズ2以降はログイン必須。ユーザーは自分の銘柄だけを閲覧・編集・削除できる。

## 株価レポート（フェーズ3）

yfinance で現在株価と為替(USD/JPY)を取得し、評価額・損益・売買判定を計算する。
米国株もドル価格を円換算し、日本株と同じ円建てで揃える。

### 評価レポートの確認（ローカル）

開発サーバーを起動し、ログインした状態で次のURLを開くと、自分の保有銘柄の
現在価格・評価額・損益・判定が JSON で見られる（ネット接続が必要）:

```
http://127.0.0.1:8000/api/report/
```

### メール送信の仕組み

- Django: `/api/report/all/?token=...` が全ユーザーのレポートを JSON で返す
  （`REPORT_API_TOKEN` 環境変数と一致する token が必要）
- `scripts/send_report.py`: その JSON を読み、各ユーザーへメール送信
- `.github/workflows/daily_report.yml`: 毎朝 JST 9:00 に上のスクリプトを実行

メール認証情報（`MAIL_USERNAME` / `MAIL_PASSWORD`）が無いときはドライランになり、
送信せずに内容を表示する。ローカルで中身を確認する例:

```bash
# 別ターミナルで開発サーバーを起動しておく
$env:REPORT_API_TOKEN = "test-token"   # PowerShell の場合
python manage.py runserver

# さらに別ターミナルで（同じトークンを指定）
$env:REPORT_API_URL  = "http://127.0.0.1:8000/api/report/all/"
$env:REPORT_API_TOKEN = "test-token"
python scripts/send_report.py          # MAIL_* 未設定なら内容を表示するだけ
```

実際の定期送信は、アプリを公開（フェーズ4）し、GitHub Secrets に
`REPORT_API_URL` / `REPORT_API_TOKEN` / `MAIL_USERNAME` / `MAIL_PASSWORD` を
設定すると有効になる。

## テスト

```bash
python manage.py test
```

## ディレクトリ構成

```
config/            # プロジェクト設定（settings.py / urls.py など）
stocks/            # 銘柄管理アプリ
  models.py        # Stock モデル（銘柄1件の定義。owner で持ち主を管理）
  forms.py         # 追加・編集フォーム
  views.py         # CRUD の汎用クラスビュー + 評価レポートAPI
  services.py      # 株価取得（yfinance）と評価額・損益・判定の計算
  urls.py          # stocks アプリのURL
  admin.py         # 管理画面の設定
  templates/       # HTML テンプレート（base / 一覧 / フォーム / ログイン）
  fixtures/        # 初期データ（initial_stocks.json）
  tests.py         # CRUD / データ分離 / 計算 / API のテスト
scripts/
  send_report.py   # レポートAPIを読んでメール送信（GitHub Actions から実行）
.github/workflows/
  daily_report.yml # 毎朝 JST 9:00 にメール送信するワークフロー
```

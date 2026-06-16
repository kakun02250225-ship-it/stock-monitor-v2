# stock-monitor-v2

PayPay証券で保有している銘柄を Web 上で管理し、毎朝その評価額・損益・売買判定をメールで受け取るためのアプリ。

詳しい背景・設計は `PROJECT.md`（引き継ぎ書）を参照。

## 開発フェーズ

- [x] **フェーズ1**: 自分1人用の CRUD（銘柄の追加・表示・編集・削除）  ← イマココ
- [ ] フェーズ2: ログイン認証 + ユーザーごとのデータ分離
- [ ] フェーズ3: 株価取得（yfinance）とメール送信（GitHub Actions 連携）
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

# 3. 初期データ（v1から引き継いだ3銘柄）を入れる ※任意
python manage.py loaddata initial_stocks

# 4. 開発サーバーを起動
python manage.py runserver
```

起動後、ブラウザで http://127.0.0.1:8000/ を開くと保有銘柄の一覧が表示される。

## テスト

```bash
python manage.py test
```

## ディレクトリ構成（フェーズ1）

```
config/            # プロジェクト設定（settings.py / urls.py など）
stocks/            # 銘柄管理アプリ
  models.py        # Stock モデル（銘柄1件の定義）
  forms.py         # 追加・編集フォーム
  views.py         # CRUD の汎用クラスビュー
  urls.py          # stocks アプリのURL
  admin.py         # 管理画面の設定
  templates/       # HTML テンプレート
  fixtures/        # 初期データ（initial_stocks.json）
  tests.py         # CRUD のテスト
```

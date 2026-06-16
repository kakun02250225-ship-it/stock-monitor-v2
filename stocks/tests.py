from decimal import Decimal
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Stock
from . import services


class StockCrudTests(TestCase):
    """ログイン中ユーザー自身の銘柄に対するCRUDが動くことを確認する。"""

    def setUp(self):
        self.user = User.objects.create_user(username="me", password="pass12345")
        self.client.login(username="me", password="pass12345")
        self.stock = Stock.objects.create(
            owner=self.user,
            name="任天堂", ticker="7974.T", market="jp",
            shares=Decimal("1.0035545904"), cost=10000,
        )

    def test_list_shows_own_stock(self):
        res = self.client.get(reverse("stocks:list"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "任天堂")

    def test_create_sets_owner_to_self(self):
        """フォームに owner 欄が無くても、保存時に持ち主が自分になる。"""
        res = self.client.post(reverse("stocks:add"), {
            "name": "日立製作所", "ticker": "6501.T", "market": "jp",
            "shares": "0.9075014067", "cost": "4500",
        })
        self.assertRedirects(res, reverse("stocks:list"))
        new = Stock.objects.get(ticker="6501.T")
        self.assertEqual(new.owner, self.user)

    def test_update_own_stock(self):
        res = self.client.post(reverse("stocks:edit", args=[self.stock.pk]), {
            "name": "任天堂", "ticker": "7974.T", "market": "jp",
            "shares": "1.0035545904", "cost": "12000",
        })
        self.assertRedirects(res, reverse("stocks:list"))
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.cost, 12000)

    def test_delete_own_stock(self):
        res = self.client.post(reverse("stocks:delete", args=[self.stock.pk]))
        self.assertRedirects(res, reverse("stocks:list"))
        self.assertEqual(Stock.objects.count(), 0)


class AuthRequiredTests(TestCase):
    """未ログインでは使えず、ログインページへ飛ばされることを確認する。"""

    def test_list_requires_login(self):
        res = self.client.get(reverse("stocks:list"))
        # 未ログインなのでログインページへリダイレクトされる（200で一覧は出ない）
        self.assertEqual(res.status_code, 302)
        self.assertIn("/accounts/login/", res.url)


class DataIsolationTests(TestCase):
    """他人の銘柄が見えない・編集できない・削除できないことを確認する（セキュリティの肝）。"""

    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="pass12345")
        self.bob = User.objects.create_user(username="bob", password="pass12345")
        # bob の銘柄
        self.bob_stock = Stock.objects.create(
            owner=self.bob,
            name="ボブの株", ticker="9999.T", market="jp",
            shares=Decimal("1.0"), cost=1000,
        )
        # alice としてログイン
        self.client.login(username="alice", password="pass12345")

    def test_list_hides_others_stock(self):
        """一覧に他人(bob)の銘柄が出ない。"""
        res = self.client.get(reverse("stocks:list"))
        self.assertNotContains(res, "ボブの株")

    def test_cannot_edit_others_stock(self):
        """他人の銘柄IDをURLに打っても編集できない（404）。"""
        res = self.client.get(reverse("stocks:edit", args=[self.bob_stock.pk]))
        self.assertEqual(res.status_code, 404)

    def test_cannot_delete_others_stock(self):
        """他人の銘柄を削除できない（404）。データも残る。"""
        res = self.client.post(reverse("stocks:delete", args=[self.bob_stock.pk]))
        self.assertEqual(res.status_code, 404)
        self.assertTrue(Stock.objects.filter(pk=self.bob_stock.pk).exists())


class EvaluationTests(TestCase):
    """評価額・損益・判定の計算ロジック（円建て統一）を検証する。"""

    def setUp(self):
        self.user = User.objects.create_user(username="me", password="x")

    def test_judge_thresholds(self):
        self.assertEqual(services.judge(Decimal("25")), "利確検討")
        self.assertEqual(services.judge(Decimal("-15")), "損切り検討")
        self.assertEqual(services.judge(Decimal("5")), "ホールド")

    def test_evaluate_jp(self):
        """日本株: 評価額 = 価格 × 株数、損益 = 評価額 − cost。"""
        stock = Stock(owner=self.user, name="任天堂", ticker="7974.T",
                      market="jp", shares=Decimal("1.0035545904"), cost=10000)
        ev = services.evaluate(stock, price=Decimal("12000"), usdjpy=None)
        self.assertEqual(ev["value"], 12043)   # 12000 × 1.00355... を四捨五入
        self.assertEqual(ev["judgment"], "利確検討")

    def test_evaluate_us_converted_to_yen(self):
        """米国株: 価格も元本(buy_price)も同じドル建てとして円に換算する。"""
        stock = Stock(owner=self.user, name="SOXL", ticker="SOXL",
                      market="us", shares=Decimal("160.36"), buy_price=41726)
        ev = services.evaluate(stock, price=Decimal("272.5"), usdjpy=Decimal("160"))
        # 元本もドル建て → 円換算: 41726 × 160
        self.assertEqual(ev["cost"], 6676160)
        # 約 +4.7% のゆるやかな利益なので「ホールド」になる
        self.assertEqual(ev["judgment"], "ホールド")
        self.assertAlmostEqual(ev["return_pct"], 4.72, delta=0.1)


class ReportApiTests(TestCase):
    """評価レポートAPIの動作と、全ユーザーAPIのトークン保護を検証する。"""

    def setUp(self):
        self.user = User.objects.create_user(username="me", password="pass12345")
        Stock.objects.create(owner=self.user, name="任天堂", ticker="7974.T",
                             market="jp", shares=Decimal("1.0"), cost=10000)

    @mock.patch.object(services, "fetch_usdjpy", return_value=Decimal("150"))
    @mock.patch.object(services, "fetch_price", return_value=Decimal("12000"))
    def test_report_api_returns_evaluation(self, _price, _fx):
        self.client.login(username="me", password="pass12345")
        res = self.client.get(reverse("stocks:report_api"))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["items"][0]["ticker"], "7974.T")
        self.assertEqual(data["items"][0]["value"], 12000)

    def test_report_api_requires_login(self):
        res = self.client.get(reverse("stocks:report_api"))
        self.assertEqual(res.status_code, 302)  # 未ログインはログインへ

    @override_settings(REPORT_API_TOKEN="secret")
    def test_report_all_rejects_wrong_token(self):
        res = self.client.get(reverse("stocks:report_all_api"), {"token": "wrong"})
        self.assertEqual(res.status_code, 403)

    @override_settings(REPORT_API_TOKEN="secret")
    @mock.patch.object(services, "fetch_usdjpy", return_value=Decimal("150"))
    @mock.patch.object(services, "fetch_price", return_value=Decimal("12000"))
    def test_report_all_accepts_correct_token(self, _price, _fx):
        res = self.client.get(reverse("stocks:report_all_api"), {"token": "secret"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()["reports"]), 1)

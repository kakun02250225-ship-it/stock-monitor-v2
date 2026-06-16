from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Stock


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

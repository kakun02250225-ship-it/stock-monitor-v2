from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Stock


class StockCrudTests(TestCase):
    """フェーズ1のCRUD（追加・一覧・編集・削除）が動くことを確認する。"""

    def setUp(self):
        # 各テストの前に1件用意しておく
        self.stock = Stock.objects.create(
            name="任天堂", ticker="7974.T", market="jp",
            shares=Decimal("1.0035545904"), cost=10000,
        )

    def test_list_shows_stock(self):
        """一覧ページに登録済みの銘柄名が表示される。"""
        res = self.client.get(reverse("stocks:list"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "任天堂")

    def test_create_stock(self):
        """フォーム送信で銘柄が1件増える。"""
        res = self.client.post(reverse("stocks:add"), {
            "name": "日立製作所", "ticker": "6501.T", "market": "jp",
            "shares": "0.9075014067", "cost": "4500",
        })
        self.assertRedirects(res, reverse("stocks:list"))
        self.assertEqual(Stock.objects.count(), 2)

    def test_update_stock(self):
        """編集で内容が更新される。"""
        res = self.client.post(reverse("stocks:edit", args=[self.stock.pk]), {
            "name": "任天堂", "ticker": "7974.T", "market": "jp",
            "shares": "1.0035545904", "cost": "12000",
        })
        self.assertRedirects(res, reverse("stocks:list"))
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.cost, 12000)

    def test_delete_stock(self):
        """削除で銘柄が消える。"""
        res = self.client.post(reverse("stocks:delete", args=[self.stock.pk]))
        self.assertRedirects(res, reverse("stocks:list"))
        self.assertEqual(Stock.objects.count(), 0)

from unittest.mock import patch


SAMPLE_ORDER = {
    "customer_email": "test@example.com",
    "items": [
        {
            "product_id": "prod-1",
            "product_name": "Keyboard",
            "quantity": 2,
            "unit_price": 49.99,
        },
        {
            "product_id": "prod-2",
            "product_name": "Mouse",
            "quantity": 1,
            "unit_price": 29.99,
        },
    ],
}


class TestHealthEndpoints:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestCreateOrder:
    @patch("app.routes.publish_order_created")
    def test_create_order_success(self, mock_publish, client):
        response = client.post("/orders", json=SAMPLE_ORDER)
        assert response.status_code == 201
        data = response.json()
        assert data["customer_email"] == "test@example.com"
        assert data["status"] == "pending"
        assert len(data["items"]) == 2
        assert data["total_amount"] == 129.97  # 2*49.99 + 1*29.99
        assert mock_publish.called

    @patch("app.routes.publish_order_created")
    def test_create_order_empty_items(self, mock_publish, client):
        response = client.post(
            "/orders",
            json={"customer_email": "test@example.com", "items": []},
        )
        assert response.status_code == 422

    @patch("app.routes.publish_order_created")
    def test_create_order_negative_quantity(self, mock_publish, client):
        order = {
            "customer_email": "test@example.com",
            "items": [
                {
                    "product_id": "prod-1",
                    "product_name": "Test",
                    "quantity": -1,
                    "unit_price": 10.0,
                }
            ],
        }
        response = client.post("/orders", json=order)
        assert response.status_code == 422


class TestGetOrder:
    @patch("app.routes.publish_order_created")
    def test_get_order(self, mock_publish, client):
        create_resp = client.post("/orders", json=SAMPLE_ORDER)
        order_id = create_resp.json()["id"]

        response = client.get(f"/orders/{order_id}")
        assert response.status_code == 200
        assert response.json()["id"] == order_id

    def test_get_order_not_found(self, client):
        response = client.get("/orders/nonexistent")
        assert response.status_code == 404


class TestListOrders:
    @patch("app.routes.publish_order_created")
    def test_list_orders(self, mock_publish, client):
        client.post("/orders", json=SAMPLE_ORDER)
        client.post("/orders", json=SAMPLE_ORDER)

        response = client.get("/orders")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    @patch("app.routes.publish_order_created")
    def test_list_orders_filter_status(self, mock_publish, client):
        client.post("/orders", json=SAMPLE_ORDER)

        response = client.get("/orders?status=pending")
        assert response.json()["total"] == 1

        response = client.get("/orders?status=confirmed")
        assert response.json()["total"] == 0


class TestCancelOrder:
    @patch("app.routes.publish_order_created")
    def test_cancel_order(self, mock_publish, client):
        create_resp = client.post("/orders", json=SAMPLE_ORDER)
        order_id = create_resp.json()["id"]

        response = client.post(f"/orders/{order_id}/cancel")
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    def test_cancel_nonexistent(self, client):
        response = client.post("/orders/nonexistent/cancel")
        assert response.status_code == 404

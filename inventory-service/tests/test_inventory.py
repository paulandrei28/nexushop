import json


class TestHealthEndpoints:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"

    def test_ready(self, client):
        response = client.get("/ready")
        assert response.status_code == 200


class TestInventoryCRUD:
    def test_create_inventory(self, client):
        response = client.post(
            "/inventory",
            data=json.dumps({"product_id": "prod-1", "quantity": 100}),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["product_id"] == "prod-1"
        assert data["quantity"] == 100
        assert data["reserved"] == 0
        assert data["available"] == 100

    def test_get_inventory(self, client):
        client.post(
            "/inventory",
            data=json.dumps({"product_id": "prod-1", "quantity": 50}),
            content_type="application/json",
        )
        response = client.get("/inventory/prod-1")
        assert response.status_code == 200
        data = response.get_json()
        assert data["quantity"] == 50

    def test_get_inventory_not_found(self, client):
        response = client.get("/inventory/nonexistent")
        assert response.status_code == 404

    def test_add_stock(self, client):
        client.post(
            "/inventory",
            data=json.dumps({"product_id": "prod-1", "quantity": 50}),
            content_type="application/json",
        )
        response = client.post(
            "/inventory/prod-1/add",
            data=json.dumps({"quantity": 25}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["quantity"] == 75

    def test_list_inventory(self, client):
        client.post(
            "/inventory",
            data=json.dumps({"product_id": "prod-1", "quantity": 10}),
            content_type="application/json",
        )
        client.post(
            "/inventory",
            data=json.dumps({"product_id": "prod-2", "quantity": 20}),
            content_type="application/json",
        )
        response = client.get("/inventory")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["items"]) == 2


class TestReservation:
    def test_reserve_stock_success(self, client):
        client.post(
            "/inventory",
            data=json.dumps({"product_id": "prod-1", "quantity": 100}),
            content_type="application/json",
        )
        response = client.post(
            "/inventory/prod-1/reserve",
            data=json.dumps({"order_id": "order-1", "quantity": 5}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "reserved"
        assert data["quantity"] == 5

        # Check available decreased
        inv = client.get("/inventory/prod-1").get_json()
        assert inv["reserved"] == 5
        assert inv["available"] == 95

    def test_reserve_stock_insufficient(self, client):
        client.post(
            "/inventory",
            data=json.dumps({"product_id": "prod-1", "quantity": 3}),
            content_type="application/json",
        )
        response = client.post(
            "/inventory/prod-1/reserve",
            data=json.dumps({"order_id": "order-1", "quantity": 10}),
            content_type="application/json",
        )
        assert response.status_code == 409
        data = response.get_json()
        assert data["available"] == 3

    def test_confirm_reservation(self, client):
        client.post(
            "/inventory",
            data=json.dumps({"product_id": "prod-1", "quantity": 100}),
            content_type="application/json",
        )
        client.post(
            "/inventory/prod-1/reserve",
            data=json.dumps({"order_id": "order-1", "quantity": 10}),
            content_type="application/json",
        )
        response = client.post("/inventory/reservations/order-1/confirm")
        assert response.status_code == 200

        # Stock permanently reduced
        inv = client.get("/inventory/prod-1").get_json()
        assert inv["quantity"] == 90
        assert inv["reserved"] == 0

    def test_release_reservation(self, client):
        client.post(
            "/inventory",
            data=json.dumps({"product_id": "prod-1", "quantity": 100}),
            content_type="application/json",
        )
        client.post(
            "/inventory/prod-1/reserve",
            data=json.dumps({"order_id": "order-1", "quantity": 10}),
            content_type="application/json",
        )
        response = client.post("/inventory/reservations/order-1/release")
        assert response.status_code == 200

        # Stock restored
        inv = client.get("/inventory/prod-1").get_json()
        assert inv["quantity"] == 100
        assert inv["reserved"] == 0
        assert inv["available"] == 100

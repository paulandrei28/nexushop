import json


SAMPLE_PRODUCT = {
    "name": "Wireless Keyboard",
    "description": "Ergonomic wireless keyboard with backlit keys",
    "price": 49.99,
    "category": "Electronics",
    "image_url": "https://example.com/keyboard.jpg",
}


class TestHealthEndpoints:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"

    def test_ready(self, client):
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.get_json()
        assert data["service"] == "product-service-test"
        assert "uptime_seconds" in data


class TestCreateProduct:
    def test_create_product_success(self, client):
        response = client.post(
            "/products",
            data=json.dumps(SAMPLE_PRODUCT),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == SAMPLE_PRODUCT["name"]
        assert data["price"] == SAMPLE_PRODUCT["price"]
        assert data["category"] == SAMPLE_PRODUCT["category"]
        assert "id" in data
        assert "created_at" in data

    def test_create_product_missing_name(self, client):
        response = client.post(
            "/products",
            data=json.dumps({"price": 10.0, "category": "Test"}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "Name is required" in data["errors"]

    def test_create_product_missing_price(self, client):
        response = client.post(
            "/products",
            data=json.dumps({"name": "Test", "category": "Test"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_product_negative_price(self, client):
        product = {**SAMPLE_PRODUCT, "price": -5.0}
        response = client.post(
            "/products",
            data=json.dumps(product),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_create_product_no_body(self, client):
        response = client.post("/products", content_type="application/json")
        assert response.status_code == 400


class TestGetProduct:
    def test_get_product(self, client):
        # Create
        create_resp = client.post(
            "/products",
            data=json.dumps(SAMPLE_PRODUCT),
            content_type="application/json",
        )
        product_id = create_resp.get_json()["id"]

        # Retrieve
        response = client.get(f"/products/{product_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == product_id
        assert data["name"] == SAMPLE_PRODUCT["name"]

    def test_get_product_not_found(self, client):
        response = client.get("/products/nonexistent-id")
        assert response.status_code == 404


class TestListProducts:
    def test_list_products_empty(self, client):
        response = client.get("/products")
        assert response.status_code == 200
        data = response.get_json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_products_with_data(self, client):
        # Create two products
        for name in ("Product A", "Product B"):
            client.post(
                "/products",
                data=json.dumps({**SAMPLE_PRODUCT, "name": name}),
                content_type="application/json",
            )

        response = client.get("/products")
        assert response.status_code == 200
        data = response.get_json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_list_products_filter_by_category(self, client):
        client.post(
            "/products",
            data=json.dumps({**SAMPLE_PRODUCT, "category": "Books"}),
            content_type="application/json",
        )
        client.post(
            "/products",
            data=json.dumps(SAMPLE_PRODUCT),
            content_type="application/json",
        )

        response = client.get("/products?category=Books")
        data = response.get_json()
        assert data["total"] == 1
        assert data["items"][0]["category"] == "Books"

    def test_list_products_search(self, client):
        client.post(
            "/products",
            data=json.dumps({**SAMPLE_PRODUCT, "name": "Special Widget"}),
            content_type="application/json",
        )
        client.post(
            "/products",
            data=json.dumps(SAMPLE_PRODUCT),
            content_type="application/json",
        )

        response = client.get("/products?search=widget")
        data = response.get_json()
        assert data["total"] == 1

    def test_list_products_pagination(self, client):
        for i in range(5):
            client.post(
                "/products",
                data=json.dumps({**SAMPLE_PRODUCT, "name": f"Product {i}"}),
                content_type="application/json",
            )

        response = client.get("/products?page=1&per_page=2")
        data = response.get_json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["pages"] == 3


class TestUpdateProduct:
    def test_update_product(self, client):
        create_resp = client.post(
            "/products",
            data=json.dumps(SAMPLE_PRODUCT),
            content_type="application/json",
        )
        product_id = create_resp.get_json()["id"]

        response = client.put(
            f"/products/{product_id}",
            data=json.dumps({"name": "Updated Name", "price": 59.99}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "Updated Name"
        assert data["price"] == 59.99

    def test_update_product_not_found(self, client):
        response = client.put(
            "/products/nonexistent",
            data=json.dumps({"name": "Test"}),
            content_type="application/json",
        )
        assert response.status_code == 404


class TestDeleteProduct:
    def test_delete_product(self, client):
        create_resp = client.post(
            "/products",
            data=json.dumps(SAMPLE_PRODUCT),
            content_type="application/json",
        )
        product_id = create_resp.get_json()["id"]

        # Delete (soft)
        response = client.delete(f"/products/{product_id}")
        assert response.status_code == 200

        # Should not be visible anymore
        response = client.get(f"/products/{product_id}")
        assert response.status_code == 404

    def test_delete_product_not_found(self, client):
        response = client.delete("/products/nonexistent")
        assert response.status_code == 404


class TestCategories:
    def test_list_categories(self, client):
        for cat in ("Electronics", "Books", "Electronics"):
            client.post(
                "/products",
                data=json.dumps({**SAMPLE_PRODUCT, "category": cat}),
                content_type="application/json",
            )

        response = client.get("/products/categories")
        assert response.status_code == 200
        data = response.get_json()
        assert sorted(data["categories"]) == ["Books", "Electronics"]

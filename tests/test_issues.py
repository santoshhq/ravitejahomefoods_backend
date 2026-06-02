"""
Test suite for Issues Router endpoints
"""
import pytest
from fastapi.testclient import TestClient
from io import BytesIO


def test_create_issue_cancel_order_without_images(client):
    """Test POST /issues/create with Cancel Order type (images optional)"""
    
    # Dummy data for cancel order issue
    dummy_data = {
        "order_id": "ORD-12345",
        "payment_id": "PAY-67890",
        "email": "customer@example.com",
        "mobile": "9876543210",
        "issue_type": "Cancel Order",
        "detailed_reason": "I want to cancel this order because I changed my mind about the purchase",
    }
    
    response = client.post("/issues/create", data=dummy_data)
    
    # Should succeed since images are optional for Cancel Order
    assert response.status_code == 200
    data = response.json()
    assert data["order_id"] == "ORD-12345"
    assert data["payment_id"] == "PAY-67890"
    assert data["email"] == "customer@example.com"
    assert data["issue_type"] == "Cancel Order"
    assert data["status"] == "Pending"
    assert "issue_id" in data


def test_create_issue_cancel_order_with_images(client):
    """Test POST /issues/create with Cancel Order type and optional images"""
    
    # Create a dummy image file
    image_data = BytesIO(b"fake image content")
    
    dummy_data = {
        "order_id": "ORD-54321",
        "payment_id": "PAY-98765",
        "email": "buyer@example.com",
        "mobile": "8765432109",
        "issue_type": "Cancel Order",
        "detailed_reason": "Canceling order due to unavailability of payment method",
    }
    
    files = [("files", ("image.jpg", image_data, "image/jpeg"))]
    
    response = client.post("/issues/create", data=dummy_data, files=files)
    
    # Should succeed with optional images
    assert response.status_code == 200
    data = response.json()
    assert data["issue_type"] == "Cancel Order"
    assert data["status"] == "Pending"


def test_create_issue_invalid_issue_type(client):
    """Test POST /issues/create with invalid issue_type"""
    
    dummy_data = {
        "order_id": "ORD-11111",
        "payment_id": "PAY-22222",
        "email": "user@example.com",
        "mobile": "9999999999",
        "issue_type": "Invalid Type",  # Invalid type
        "detailed_reason": "This is an invalid issue type",
    }
    
    response = client.post("/issues/create", data=dummy_data)
    
    assert response.status_code == 400
    assert "Invalid issue_type" in response.json()["detail"]


def test_create_issue_refund_without_images_should_fail(client):
    """Test POST /issues/create with Refund/Return without images (should fail)"""
    
    dummy_data = {
        "order_id": "ORD-33333",
        "payment_id": "PAY-44444",
        "email": "refund@example.com",
        "mobile": "7777777777",
        "issue_type": "Refund/Return",
        "detailed_reason": "Product arrived damaged and needs refund",
    }
    
    response = client.post("/issues/create", data=dummy_data)
    
    # Should fail because Refund/Return requires images
    assert response.status_code == 400
    assert "Images are required" in response.json()["detail"]


def test_create_issue_replace_order_without_images_should_fail(client):
    """Test POST /issues/create with Replace Order without images (should fail)"""
    
    dummy_data = {
        "order_id": "ORD-55555",
        "payment_id": "PAY-66666",
        "email": "replace@example.com",
        "mobile": "6666666666",
        "issue_type": "Replace Order",
        "detailed_reason": "Need to replace entire order",
    }
    
    response = client.post("/issues/create", data=dummy_data)
    
    # Should fail because Replace Order requires images
    assert response.status_code == 400
    assert "Images are required" in response.json()["detail"]


def test_create_issue_missing_required_fields(client):
    """Test POST /issues/create with missing required fields"""
    
    # Missing 'email' field
    dummy_data = {
        "order_id": "ORD-77777",
        "payment_id": "PAY-88888",
        "mobile": "5555555555",
        "issue_type": "Cancel Order",
        "detailed_reason": "Missing email field",
    }
    
    response = client.post("/issues/create", data=dummy_data)
    
    # Should fail with validation error
    assert response.status_code == 422


def test_create_issue_invalid_email_format(client):
    """Test POST /issues/create with invalid email format"""
    
    dummy_data = {
        "order_id": "ORD-99999",
        "payment_id": "PAY-11111",
        "email": "invalid-email",  # Invalid email format
        "mobile": "4444444444",
        "issue_type": "Cancel Order",
        "detailed_reason": "Testing invalid email",
    }
    
    response = client.post("/issues/create", data=dummy_data)
    
    # Should fail with validation error
    assert response.status_code == 422


def test_create_issue_short_reason(client):
    """Test POST /issues/create with reason shorter than 10 characters"""
    
    dummy_data = {
        "order_id": "ORD-22222",
        "payment_id": "PAY-33333",
        "email": "test@example.com",
        "mobile": "3333333333",
        "issue_type": "Cancel Order",
        "detailed_reason": "Short",  # Less than 10 characters
    }
    
    response = client.post("/issues/create", data=dummy_data)
    
    # Should fail with validation error
    assert response.status_code == 422


def test_create_issue_short_mobile(client):
    """Test POST /issues/create with mobile number shorter than 10 digits"""
    
    dummy_data = {
        "order_id": "ORD-44444",
        "payment_id": "PAY-55555",
        "email": "test@example.com",
        "mobile": "123456789",  # Less than 10 digits
        "issue_type": "Cancel Order",
        "detailed_reason": "Testing short mobile number",
    }
    
    response = client.post("/issues/create", data=dummy_data)
    
    # Should fail with validation error
    assert response.status_code == 422


def test_get_all_issue_images(client):
    """Test GET /issues/all_images endpoint"""
    
    response = client.get("/issues/all_images")
    
    # Should return 200 and a list of image URLs
    assert response.status_code == 200
    data = response.json()
    assert "image_urls" in data
    assert isinstance(data["image_urls"], list)

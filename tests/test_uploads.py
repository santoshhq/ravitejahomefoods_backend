import io


def test_uploads_endpoints(client):
    files = [
        ("files", ("image1.png", io.BytesIO(b"data"), "image/png")),
        ("files", ("image2.jpg", io.BytesIO(b"data"), "image/jpeg")),
    ]
    upload = client.post("/imagesuploads/images", files=files)
    assert upload.status_code == 200
    assert upload.json().get("image_urls")

    get_images = client.post("/imagesuploads/get_images", json=["https://example.com/x.png"])
    assert get_images.status_code == 200

    list_images = client.get("/imagesuploads/all_images")
    assert list_images.status_code == 200

    update_images = client.put("/imagesuploads/update_images")
    assert update_images.status_code == 200

    delete_images = client.delete("/imagesuploads/delete_images", json=["https://example.com/x.png"])
    assert delete_images.status_code == 200

import io


def test_uploads_real(client):
    files = [
        ("files", ("image1.png", io.BytesIO(b"data"), "image/png")),
    ]
    upload = client.post("/imagesuploads/images", files=files)
    assert upload.status_code == 200
    image_urls = upload.json().get("image_urls", [])
    assert image_urls

    get_images = client.post("/imagesuploads/get_images", json=image_urls)
    assert get_images.status_code == 200

    list_images = client.get("/imagesuploads/all_images")
    assert list_images.status_code == 200

    delete_images = client.delete("/imagesuploads/delete_images", json=image_urls)
    assert delete_images.status_code == 200

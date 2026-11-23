"""표지를 S3에 저장하는 경우의 테스트: botocore Stubber로 S3 응답을 흉내 냅니다."""
import boto3
import pytest
from botocore.stub import ANY, Stubber

from app.config import settings
from app.services import covers
from tests.helpers import create_book

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100
BUCKET = "book-api-covers-test"

@pytest.fixture
def s3(monkeypatch):
    client = boto3.client("s3", region_name="ap-northeast-2",
                          aws_access_key_id="test", aws_secret_access_key="test")
    monkeypatch.setattr(covers, "_s3", lambda: client)
    monkeypatch.setattr(settings, "cover_bucket", BUCKET)
    with Stubber(client) as stubber:
        yield stubber

def test_upload_saves_to_s3(client, auth_headers, author_id, s3):
    book = create_book(client, auth_headers, author_id)
    s3.add_response("put_object", {}, {"Bucket": BUCKET, "Key": ANY, "Body": PNG, "ContentType": "image/png"})

    response = client.post(f"/books/{book['id']}/cover", headers=auth_headers,
                           files={"file": ("cover.png", PNG, "image/png")})

    assert response.status_code == 200
    assert response.json()["cover_url"].startswith("/covers/")
    s3.assert_no_pending_responses()  # put_object가 정확히 한 번 불렸는지 확인합니다.

def test_cover_redirects_to_presigned_url(client, s3):
    name = "a" * 32 + ".png"
    response = client.get(f"/covers/{name}", follow_redirects=False)

    assert response.status_code == 307
    location = response.headers["location"]
    assert BUCKET in location and f"covers/{name}" in location
    assert "X-Amz-Signature=" in location and "X-Amz-Expires=300" in location

@pytest.mark.parametrize("name", ["..%2Fsecret.txt", "evil.html", "A" * 32 + ".png"])
def test_cover_rejects_unexpected_names(client, s3, name):
    assert client.get(f"/covers/{name}", follow_redirects=False).status_code == 404

import base64
from unittest.mock import MagicMock, patch
import pytest
from app.utils.storage import (
    get_supabase_client,
    parse_base64_image,
    upload_base64_to_supabase,
    delete_file_from_supabase,
)


def test_parse_base64_image_data_uri():
    sample_text = "test image data"
    b64_encoded = base64.b64encode(sample_text.encode("utf-8")).decode("utf-8")
    data_uri = f"data:image/png;base64,{b64_encoded}"

    file_bytes, mime, ext = parse_base64_image(data_uri)
    assert file_bytes == sample_text.encode("utf-8")
    assert mime == "image/png"
    assert ext == "png"


def test_parse_base64_image_raw():
    sample_text = "raw jpeg data"
    b64_encoded = base64.b64encode(sample_text.encode("utf-8")).decode("utf-8")

    file_bytes, mime, ext = parse_base64_image(b64_encoded)
    assert file_bytes == sample_text.encode("utf-8")
    assert mime == "image/jpeg"
    assert ext == "jpg"


def test_upload_base64_returns_existing_url():
    url = "https://cdn.example.com/images/prod1.jpg"
    assert upload_base64_to_supabase(url) == url


def test_upload_base64_empty():
    assert upload_base64_to_supabase("") == ""


def test_upload_base64_invalid_string():
    # Non-base64 invalid data
    assert upload_base64_to_supabase("invalid base64 @@@") == "invalid base64 @@@"


def test_upload_base64_with_mocked_supabase(app):
    with app.app_context():
        sample_text = "hello binary"
        b64_encoded = f"data:image/webp;base64,{base64.b64encode(sample_text.encode('utf-8')).decode('utf-8')}"

        mock_client = MagicMock()
        mock_storage = MagicMock()
        mock_from = MagicMock()

        mock_client.storage = mock_storage
        mock_storage.from_.return_value = mock_from
        mock_from.get_public_url.return_value = "https://supabase.co/storage/v1/object/public/products/products/test.webp"

        with patch("app.utils.storage.get_supabase_client", return_value=mock_client):
            res_url = upload_base64_to_supabase(b64_encoded)
            assert "https://supabase.co/storage/v1/object/public/products/products/test.webp" == res_url
            mock_from.upload.assert_called_once()


def test_upload_base64_client_unavailable_fallback(app):
    with app.app_context():
        sample_text = "fallback test"
        b64_encoded = f"data:image/png;base64,{base64.b64encode(sample_text.encode('utf-8')).decode('utf-8')}"

        with patch("app.utils.storage.get_supabase_client", return_value=None):
            res_url = upload_base64_to_supabase(b64_encoded)
            assert "https://mock-supabase.local/storage/v1/object/public/products/" in res_url


def test_upload_base64_upload_exception(app):
    with app.app_context():
        sample_text = "exception test"
        b64_encoded = f"data:image/png;base64,{base64.b64encode(sample_text.encode('utf-8')).decode('utf-8')}"

        mock_client = MagicMock()
        mock_storage = MagicMock()
        mock_from = MagicMock()
        mock_client.storage = mock_storage
        mock_storage.from_.return_value = mock_from
        mock_from.upload.side_effect = Exception("Storage error")

        with patch("app.utils.storage.get_supabase_client", return_value=mock_client):
            res_url = upload_base64_to_supabase(b64_encoded)
            assert "/storage/v1/object/public/products/" in res_url



def test_delete_file_from_supabase_mocked(app):
    with app.app_context():
        mock_client = MagicMock()
        mock_storage = MagicMock()
        mock_from = MagicMock()

        mock_client.storage = mock_storage
        mock_storage.from_.return_value = mock_from

        with patch("app.utils.storage.get_supabase_client", return_value=mock_client):
            url = "https://shgafjqeprksdawepfcl.supabase.co/storage/v1/object/public/products/products/abc.png"
            success = delete_file_from_supabase(url)
            assert success is True
            mock_from.remove.assert_called_once_with(["products/abc.png"])


def test_delete_file_from_supabase_raw_path(app):
    with app.app_context():
        mock_client = MagicMock()
        mock_storage = MagicMock()
        mock_from = MagicMock()

        mock_client.storage = mock_storage
        mock_storage.from_.return_value = mock_from

        with patch("app.utils.storage.get_supabase_client", return_value=mock_client):
            success = delete_file_from_supabase("products/raw_image.jpg")
            assert success is True
            mock_from.remove.assert_called_once_with(["products/raw_image.jpg"])


def test_delete_file_from_supabase_empty_or_no_client(app):
    assert delete_file_from_supabase("") is False
    with app.app_context():
        with patch("app.utils.storage.get_supabase_client", return_value=None):
            assert delete_file_from_supabase("https://example.com/test.jpg") is False


def test_delete_file_from_supabase_exception(app):
    with app.app_context():
        mock_client = MagicMock()
        mock_storage = MagicMock()
        mock_from = MagicMock()
        mock_client.storage = mock_storage
        mock_storage.from_.return_value = mock_from
        mock_from.remove.side_effect = Exception("Delete error")

        with patch("app.utils.storage.get_supabase_client", return_value=mock_client):
            success = delete_file_from_supabase("products/test.png")
            assert success is False


def test_get_supabase_client_missing_config(app):
    with app.app_context():
        with patch.dict(app.config, {"SUPABASE_URL": "", "SUPABASE_KEY": ""}):
            with patch("app.utils.storage._supabase_client", None):
                client = get_supabase_client()
                assert client is None


def test_get_supabase_client_init_exception(app):
    with app.app_context():
        with patch.dict(app.config, {"SUPABASE_URL": "http://invalid", "SUPABASE_KEY": "dummy"}):
            with patch("app.utils.storage._supabase_client", None):
                with patch("app.utils.storage.create_client", side_effect=Exception("Init error")):
                    client = get_supabase_client()
                    assert client is None

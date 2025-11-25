import pytest


@pytest.mark.usefixtures("db_session")
def test_index(app):
    """Test that the index page is working"""

    with app.test_client() as client:
        res = client.get("/")
        assert res.status_code == 200
        assert res.text == "Hello! This is the UUID API service :)"


@pytest.mark.usefixtures("db_session")
def test_status(app):
    """Test that the status endpoint is working"""

    with app.test_client() as client:
        res = client.get("/status")
        assert res.status_code == 200
        data = res.get_json()
        assert "version" in data
        assert "build" in data
        assert data["mysql_connection"] is True

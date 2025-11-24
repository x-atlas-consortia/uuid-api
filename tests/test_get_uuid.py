import uuid
import pytest

from tests.helpers import USER, calculate_checksum
from tests.helpers.auth import AUTH_TOKEN
from tests.helpers.database import create_file, create_files, create_provenance


@pytest.mark.parametrize(
    "prov_list",
    [
        ("data_center", "source"),
        ("data_center", "source", "organ"),
        ("data_center", "source", "organ", "block"),
        ("data_center", "source", "organ", "block", "section"),
        ("data_center", "source", "organ", "block", "section", "dataset"),
    ],
)
def test_get_uuid_by_uuid(app, db_session, prov_list):
    """Test retrieving UUID information by UUID value via the GET /uuid/<uuid> endpoint"""

    prov = create_provenance(db_session, prov_list)
    ancestor = prov[prov_list[-2]]
    uuid_item = prov[prov_list[-1]]

    with app.test_client() as client:
        res = client.get(
            f"/uuid/{uuid_item['uuid']}",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        )
        assert res.status_code == 200
        data = res.get_json()

        assert data["ancestor_id"] == ancestor["uuid"]
        assert data["ancestor_ids"] == [ancestor["uuid"]]
        assert data["email"] == USER["email"]
        assert data["hm_uuid"] == uuid_item["uuid"]
        assert data["sennet_id"] == uuid_item["entity_id"]
        assert data["time_generated"] == uuid_item["time_generated"].strftime("%Y-%m-%d %H:%M:%S")
        assert data["type"] == uuid_item["entity_type"]
        assert data["user_id"] == USER["sub"]
        assert data["uuid"] == uuid_item["uuid"]


@pytest.mark.parametrize(
    "prov_list",
    [
        ("data_center", "source"),
        ("data_center", "source", "organ"),
        ("data_center", "source", "organ", "block"),
        ("data_center", "source", "organ", "block", "section"),
        ("data_center", "source", "organ", "block", "section", "dataset"),
    ],
)
def test_get_uuid_by_id(app, db_session, prov_list):
    """Test retrieving UUID information by entity ID (SNT...) via the GET /uuid/<uuid> endpoint"""

    prov = create_provenance(db_session, prov_list)
    ancestor = prov[prov_list[-2]]  # second to last item of the provenance
    uuid_item = prov[prov_list[-1]]  # last item of the provenance

    with app.test_client() as client:
        res = client.get(
            f"/uuid/{uuid_item['entity_id']}",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        )
        assert res.status_code == 200
        data = res.get_json()

        assert data["ancestor_id"] == ancestor["uuid"]
        assert data["ancestor_ids"] == [ancestor["uuid"]]
        assert data["email"] == USER["email"]
        assert data["hm_uuid"] == uuid_item["uuid"]
        assert data["sennet_id"] == uuid_item["entity_id"]
        assert data["time_generated"] == uuid_item["time_generated"].strftime("%Y-%m-%d %H:%M:%S")
        assert data["type"] == uuid_item["entity_type"]
        assert data["user_id"] == USER["sub"]
        assert data["uuid"] == uuid_item["uuid"]


def test_get_file_by_id(app, db_session):
    """Test retrieving File UUID information by UUID value via the GET /uuid/<uuid> endpoint"""

    prov = create_provenance(db_session, ["source", "organ", "block", "section", "dataset"])
    file = create_file(
        db_session,
        {
            "path": "basepath/test_file.txt",
            "size": 12345,
            "sha256_checksum": calculate_checksum("basepath/test_file.txt", "sha256"),
            "md5_checksum": calculate_checksum("basepath/test_file.txt", "md5"),
            "parent_uuid": prov["dataset"]["uuid"],
        },
    )

    with app.test_client() as client:
        res = client.get(
            f"/uuid/{file['uuid']}",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        )
        assert res.status_code == 200
        data = res.get_json()

        assert data["ancestor_id"] == prov["dataset"]["uuid"]
        assert data["ancestor_ids"] == [prov["dataset"]["uuid"]]
        assert data["email"] == USER["email"]
        assert data["hm_uuid"] == file["uuid"]
        assert data["time_generated"] == file["time_generated"].strftime("%Y-%m-%d %H:%M:%S")
        assert data["type"] == "FILE"
        assert data["user_id"] == USER["sub"]
        assert data["uuid"] == file["uuid"]


def test_get_file_info_by_id(app, db_session):
    """Test retrieving File UUID information by UUID value via the GET /file-id/<uuid> endpoint"""

    prov = create_provenance(db_session, ["source", "organ", "block", "section", "dataset"])
    file = create_file(
        db_session,
        {
            "path": "basepath/test_file.txt",
            "size": 12345,
            "sha256_checksum": calculate_checksum("basepath/test_file.txt", "sha256"),
            "md5_checksum": calculate_checksum("basepath/test_file.txt", "md5"),
            "parent_uuid": prov["dataset"]["uuid"],
        },
    )

    with app.test_client() as client:
        res = client.get(
            f"/file-id/{file['uuid']}",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        )
        assert res.status_code == 200
        data = res.get_json()

        assert data["ancestor_uuid"] == prov["dataset"]["uuid"]
        assert data["base_dir"] == "DATA_UPLOAD"
        assert data["hm_uuid"] == file["uuid"]
        assert data["md5_checksum"] == file["md5_checksum"]
        assert data["path"] == file["path"]
        assert data["sha256_checksum"] == file["sha256_checksum"]
        assert data["size"] == file["size"]
        assert data["uuid"] == file["uuid"]


def test_get_files_for_dataset(app, db_session):
    """Test retrieving all File UUIDs for a Dataset via the GET /<dataset_uuid>/files endpoint"""

    prov = create_provenance(db_session, ["source", "organ", "block", "section", "dataset"])
    dataset_uuid = prov["dataset"]["uuid"]
    files = create_files(
        db_session,
        [
            {
                "path": "basepath/test_file.txt",
                "size": 12345,
                "sha256_checksum": calculate_checksum("basepath/test_file.txt", "sha256"),
                "md5_checksum": calculate_checksum("basepath/test_file.txt", "md5"),
                "parent_uuid": dataset_uuid,
            },
            {
                "path": "basepath/test_file_2.txt",
                "size": 67890,
                "sha256_checksum": calculate_checksum("basepath/test_file_2.txt", "sha256"),
                "md5_checksum": calculate_checksum("basepath/test_file.txt_2", "md5"),
                "parent_uuid": dataset_uuid,
            },
        ],
    )

    with app.test_client() as client:
        res = client.get(
            f"/{dataset_uuid}/files",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        )
        assert res.status_code == 200
        data = res.get_json()
        assert len(data) == 2

        # sort the files by path to ensure consistent order
        data.sort(key=lambda x: x["path"])
        for file, data in zip(files, data):
            assert data["file_uuid"] == file["uuid"]
            assert data["path"] == file["path"]
            assert data["sha256_checksum"] == file["sha256_checksum"]
            assert data["md5_checksum"] == file["md5_checksum"]
            assert data["size"] == file["size"]
            assert data["base_dir"] == "DATA_UPLOAD"


@pytest.mark.parametrize(
    "exists",
    [True, False],
)
def test_uuid_exists(app, db_session, exists):
    """Test checking existence of a UUID via the GET /uuid/<uuid>/exists endpoint"""

    if exists:
        prov = create_provenance(db_session, ["source", "organ", "block", "section", "dataset"])
        item_uuid = prov["dataset"]["uuid"]
    else:
        item_uuid = uuid.uuid4().hex

    with app.test_client() as client:
        res = client.get(
            f"/uuid/{item_uuid}/exists",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        )
        assert res.status_code == 200
        assert res.text == "true" if exists else "false"


def test_uuid_ancestors(app, db_session):
    """Test retrieving ancestors of a UUID via the GET /<uuid>/ancestors endpoint"""

    prov = create_provenance(db_session, ["source", "organ", "block", "section", "dataset"])
    dataset_uuid = prov["dataset"]["uuid"]

    with app.test_client() as client:
        res = client.get(
            f"/{dataset_uuid}/ancestors",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        )
        assert res.status_code == 200
        data = res.get_json()

        assert len(data) == 1
        assert data[0] == prov["section"]["uuid"]

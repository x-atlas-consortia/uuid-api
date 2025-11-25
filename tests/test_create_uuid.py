import re

from tests.helpers import GROUP_ID, USER, calculate_checksum
from tests.helpers.auth import AUTH_TOKEN
from tests.helpers.database import create_file, create_provenance, get_uuid


def test_create_source_uuid(app, db_session):
    """Test creating a Source UUID via the POST /uuid endpoint"""

    with app.test_client() as client:
        res = client.post(
            "/uuid",
            json={"entity_type": "Source", "parent_ids": [GROUP_ID]},
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        )
        assert res.status_code == 200
        data = res.get_json()
        assert len(data) == 1

        data = data[0]
        assert re.match(r"^[a-f0-9]{32}$", data["uuid"])
        assert re.match(r"^[a-f0-9]{32}$", data["hm_uuid"])
        assert re.match(r"^[A-Z0-9]{10}$", data["base_id"])
        assert re.match(r"^SNT[0-9A-Z]{3}\.[A-Z]{4}\.[0-9]{3}$", data["sennet_id"])

        # Verify that the uuid was created in the database
        db_entry = get_uuid(uuid=data["uuid"], cnx=db_session)
        assert db_entry is not None
        assert db_entry["uuid"] == data["uuid"]
        assert db_entry["entity_type"] == "SOURCE"
        assert db_entry["user_id"] == USER["sub"]
        assert db_entry["user_email"] == USER["email"]


def test_create_organ_uuid(app, db_session):
    """Test creating an Organ UUID via the POST /uuid endpoint"""

    prov = create_provenance(db_session, ["source"])
    source = prov["source"]

    with app.test_client() as client:
        res = client.post(
            "/uuid",
            json={
                "entity_type": "Sample",
                "organ_code": "UBERON:0000178",
                "parent_ids": [source["uuid"]],
            },
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        )
        assert res.status_code == 200
        data = res.get_json()
        assert len(data) == 1

        data = data[0]
        assert re.match(r"^[a-f0-9]{32}$", data["uuid"])
        assert re.match(r"^[a-f0-9]{32}$", data["hm_uuid"])
        assert re.match(r"^[A-Z0-9]{10}$", data["base_id"])
        assert re.match(r"^SNT[0-9A-Z]{3}\.[A-Z]{4}\.[0-9]{3}$", data["sennet_id"])

        # Verify that the uuid was created in the database
        db_entry = get_uuid(uuid=data["uuid"], cnx=db_session)
        assert db_entry is not None
        assert db_entry["uuid"] == data["uuid"]
        assert db_entry["entity_type"] == "SAMPLE"
        assert db_entry["user_id"] == USER["sub"]
        assert db_entry["user_email"] == USER["email"]


def test_create_block_uuid(app, db_session):
    """Test creating a Block UUID via the POST /uuid endpoint"""

    prov = create_provenance(db_session, ["source", "organ"])
    organ = prov["organ"]

    with app.test_client() as client:
        res = client.post(
            "/uuid",
            json={
                "entity_type": "Sample",
                "parent_ids": [organ["uuid"]],
            },
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        )
        assert res.status_code == 200
        data = res.get_json()
        assert len(data) == 1

        data = data[0]
        assert re.match(r"^[a-f0-9]{32}$", data["uuid"])
        assert re.match(r"^[a-f0-9]{32}$", data["hm_uuid"])
        assert re.match(r"^[A-Z0-9]{10}$", data["base_id"])
        assert re.match(r"^SNT[0-9A-Z]{3}\.[A-Z]{4}\.[0-9]{3}$", data["sennet_id"])

        # Verify that the uuid was created in the database
        db_entry = get_uuid(uuid=data["uuid"], cnx=db_session)
        assert db_entry is not None
        assert db_entry["uuid"] == data["uuid"]
        assert db_entry["entity_type"] == "SAMPLE"
        assert db_entry["user_id"] == USER["sub"]
        assert db_entry["user_email"] == USER["email"]


def test_create_section_uuid(app, db_session):
    """Test creating a Section UUID via the POST /uuid endpoint"""

    prov = create_provenance(db_session, ["source", "organ", "block"])
    block = prov["block"]

    with app.test_client() as client:
        res = client.post(
            "/uuid",
            json={
                "entity_type": "Sample",
                "parent_ids": [block["uuid"]],
            },
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        )
        assert res.status_code == 200
        data = res.get_json()
        assert len(data) == 1

        data = data[0]
        assert re.match(r"^[a-f0-9]{32}$", data["uuid"])
        assert re.match(r"^[a-f0-9]{32}$", data["hm_uuid"])
        assert re.match(r"^[A-Z0-9]{10}$", data["base_id"])
        assert re.match(r"^SNT[0-9A-Z]{3}\.[A-Z]{4}\.[0-9]{3}$", data["sennet_id"])

        # Verify that the uuid was created in the database
        db_entry = get_uuid(uuid=data["uuid"], cnx=db_session)
        assert db_entry is not None
        assert db_entry["uuid"] == data["uuid"]
        assert db_entry["entity_type"] == "SAMPLE"
        assert db_entry["user_id"] == USER["sub"]
        assert db_entry["user_email"] == USER["email"]


def test_create_dataset_uuid(app, db_session):
    """Test creating a Dataset UUID via the POST /uuid endpoint"""

    prov = create_provenance(db_session, ["source", "organ", "block", "section"])
    section = prov["section"]

    with app.test_client() as client:
        res = client.post(
            "/uuid",
            json={
                "entity_type": "Dataset",
                "parent_ids": [section["uuid"]],
            },
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        )
        assert res.status_code == 200
        data = res.get_json()
        assert len(data) == 1

        data = data[0]
        assert re.match(r"^[a-f0-9]{32}$", data["uuid"])
        assert re.match(r"^[a-f0-9]{32}$", data["hm_uuid"])
        assert re.match(r"^[A-Z0-9]{10}$", data["base_id"])
        assert re.match(r"^SNT[0-9A-Z]{3}\.[A-Z]{4}\.[0-9]{3}$", data["sennet_id"])

        # Verify that the uuid was created in the database
        db_entry = get_uuid(uuid=data["uuid"], cnx=db_session)
        assert db_entry is not None
        assert db_entry["uuid"] == data["uuid"]
        assert db_entry["entity_type"] == "DATASET"
        assert db_entry["user_id"] == USER["sub"]
        assert db_entry["user_email"] == USER["email"]


def test_create_file_uuid(app, db_session):
    """Test creating a File UUID via the POST /uuid endpoint"""

    prov = create_provenance(db_session, ["source", "organ", "block", "section", "dataset"])
    dataset = prov["dataset"]

    path = "lab_processed/images/JDC_WP_012_n.ome.tiff"

    with app.test_client() as client:
        res = client.post(
            "/uuid",
            json={
                "entity_type": "FILE",
                "parent_ids": [dataset["uuid"]],
                "file_info": [
                    {
                        "path": path,
                        "sha256_checksum": calculate_checksum(path, "sha256"),
                        "md5_checksum": calculate_checksum(path, "md5"),
                        "size": 8464822332,
                        "base_dir": "DATA_UPLOAD",
                    }
                ],
            },
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        )
        assert res.status_code == 200
        data = res.get_json()
        assert len(data) == 1

        data = data[0]
        assert re.match(r"^ffff[a-f0-9]{28}$", data["uuid"])
        assert re.match(r"^ffff[a-f0-9]{28}$", data["hm_uuid"])
        assert data["file_path"] == "lab_processed/images/JDC_WP_012_n.ome.tiff"

        # Verify that the uuid was created in the database
        db_entry = get_uuid(uuid=data["uuid"], cnx=db_session)
        assert db_entry is not None
        assert db_entry["uuid"] == data["uuid"]
        assert db_entry["entity_type"] == "FILE"
        assert db_entry["user_id"] == USER["sub"]
        assert db_entry["user_email"] == USER["email"]


def test_create_file_uuid_path_exists(app, db_session):
    """Test creating a File UUID via the POST /uuid endpoint fails when the file path already
    exists"""

    prov = create_provenance(db_session, ["source", "organ", "block", "section", "dataset"])
    dataset = prov["dataset"]
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
        res = client.post(
            "/uuid",
            json={
                "entity_type": "FILE",
                "parent_ids": [dataset["uuid"]],
                "file_info": [
                    {
                        "path": file["path"],
                        "sha256_checksum": file["sha256_checksum"],
                        "md5_checksum": file["md5_checksum"],
                        "size": file["size"],
                        "base_dir": "DATA_UPLOAD",
                    }
                ],
            },
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        )
        assert res.status_code == 409


def test_create_multiple_file_uuids(app, db_session):
    """Test creating multiple File UUIDs via the POST /uuid endpoint"""

    prov = create_provenance(db_session, ["source", "organ", "block", "section", "dataset"])
    dataset = prov["dataset"]
    paths = [
        "lab_processed/images/JDC_WP_012_n.ome.tiff",
        "lab_processed/images/JDC_WP_014_n.ome.tiff",
    ]

    with app.test_client() as client:
        res = client.post(
            "/uuid?entity_count=2",
            json={
                "entity_type": "FILE",
                "parent_ids": [dataset["uuid"]],
                "file_info": [
                    {
                        "path": paths[0],
                        "sha256_checksum": calculate_checksum(paths[0], "sha256"),
                        "md5_checksum": calculate_checksum(paths[0], "md5"),
                        "size": 8464822332,
                        "base_dir": "DATA_UPLOAD",
                    },
                    {
                        "path": paths[1],
                        "sha256_checksum": calculate_checksum(paths[1], "sha256"),
                        "md5_checksum": calculate_checksum(paths[1], "md5"),
                        "size": 8464822332,
                        "base_dir": "DATA_UPLOAD",
                    },
                ],
            },
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        )
        assert res.status_code == 200
        data = res.get_json()
        assert len(data) == 2

        # sort the files by path to ensure consistent order
        data.sort(key=lambda x: x["file_path"])
        for path, d in zip(paths, data):
            assert re.match(r"^ffff[a-f0-9]{28}$", d["uuid"])
            assert re.match(r"^ffff[a-f0-9]{28}$", d["hm_uuid"])
            assert d["file_path"] == path

            # Verify that the uuid was created in the database
            db_entry = get_uuid(uuid=d["uuid"], cnx=db_session)
            assert db_entry is not None
            assert db_entry["uuid"] == d["uuid"]
            assert db_entry["entity_type"] == "FILE"
            assert db_entry["user_id"] == USER["sub"]
            assert db_entry["user_email"] == USER["email"]


def test_create_uuid_no_write(app, auth):
    """Test that creating a UUID via the POST /uuid endpoint fails without write privileges"""

    auth.write_privs = False

    with app.test_client() as client:
        res = client.post(
            "/uuid",
            json={"entity_type": "Source", "parent_ids": [GROUP_ID]},
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
        )
        assert res.status_code == 403

import random
import time
import uuid

import mysql.connector
import pytest
from mysql.connector import Error

from tests.helpers import CHAR_SET, GROUP, LAB, NUM_SET, USER


def wait_for_mysql(host, name, user, password, timeout=60, interval=1):
    start_time = time.time()
    last_exc = None

    while True:
        try:
            cnx = mysql.connector.connect(host=host, user=user, password=password, database=name)
            cnx.autocommit = True
            try:
                with cnx.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                print("MySQL is up and running")
                return cnx
            except Exception:
                cnx.close()
                raise
        except Error as e:
            last_exc = e
            if time.time() - start_time > timeout:
                print("Timeout waiting for MySQL to be ready")
                raise last_exc
            print("Waiting for MySQL to be ready...")
            time.sleep(interval)


@pytest.fixture(scope="session")
def db_session():
    mysql_host = "127.0.0.1"
    mysql_name = "sn_uuid"
    mysql_username = "uuid_user"
    mysql_password = "uuid_password"

    cnx = wait_for_mysql(mysql_host, mysql_name, mysql_username, mysql_password)
    lab = create_lab(cnx)
    create_data_center(cnx, lab)
    yield cnx
    cnx.close()


def create_lab(cnx):
    lab = {
        "uuid": LAB["uuid"],
        "entity_type": "LAB",
        "user_id": USER["sub"],
        "user_email": USER["email"],
    }

    # Create a lab row in uuids if it doesn't exist
    with cnx.cursor(dictionary=True) as cursor:
        cursor.execute(
            "SELECT UUID AS uuid, ENTITY_TYPE AS entity_type, TIME_GENERATED AS time_generated, "
            "USER_ID AS user_id, USER_EMAIL AS user_email "
            "FROM uuids WHERE UUID = %s",
            (lab["uuid"],),
        )
        existing = cursor.fetchone()
        if existing:
            return existing

        cursor.execute(
            "INSERT INTO uuids (UUID, ENTITY_TYPE, USER_ID, USER_EMAIL) VALUES (%s, %s, %s, %s)",
            (
                lab["uuid"],
                lab["entity_type"],
                lab["user_id"],
                lab["user_email"],
            ),
        )
        cnx.commit()

        # re-query to return the inserted row (including TIME_GENERATED)
        cursor.execute(
            "SELECT UUID AS uuid, ENTITY_TYPE AS entity_type, TIME_GENERATED AS time_generated, "
            "USER_ID AS user_id, USER_EMAIL AS user_email "
            "FROM uuids WHERE UUID = %s",
            (lab["uuid"],),
        )
        inserted = cursor.fetchone()

    return inserted


def create_data_center(cnx, lab):
    dc = {"uuid": lab["uuid"], "dc_uuid": GROUP["uuid"], "dc_code": GROUP["tmc_prefix"]}

    with cnx.cursor(dictionary=True) as cursor:
        cursor.execute(
            "SELECT UUID AS uuid, DC_UUID AS dc_uuid, DC_CODE AS dc_code FROM data_centers "
            "WHERE UUID = %s",
            (dc["uuid"],),
        )
        existing = cursor.fetchone()
        if existing:
            return existing

        cursor.execute(
            "INSERT INTO data_centers (UUID, DC_UUID, DC_CODE) VALUES (%s, %s, %s)",
            (dc["uuid"], dc["dc_uuid"], dc["dc_code"]),
        )
        cnx.commit()

        cursor.execute(
            "SELECT UUID AS uuid, DC_UUID AS dc_uuid, DC_CODE AS dc_code FROM data_centers "
            "WHERE UUID = %s",
            (dc["uuid"],),
        )
        inserted = cursor.fetchone()

    return inserted


def get_uuid(cnx, uuid):
    with cnx.cursor(dictionary=True) as cursor:
        cursor.execute(
            "SELECT UUID AS uuid, ENTITY_TYPE AS entity_type, TIME_GENERATED AS time_generated, "
            "USER_ID AS user_id, USER_EMAIL AS user_email "
            "FROM uuids WHERE UUID = %s",
            (uuid,),
        )
        row = cursor.fetchone()
        return row


def generate_uuid_item():
    first = "".join(random.choices(NUM_SET, k=3))
    second = "".join(random.choices(CHAR_SET, k=4))
    third = "".join(random.choices(NUM_SET, k=3))

    entity_id = f"SNT{first}.{second}.{third}"
    base_id = f"{first}{second}{third}"

    return {
        "uuid": uuid.uuid4().hex,
        "user_id": USER["sub"],
        "user_email": USER["email"],
        "entity_id": entity_id,
        "base_id": base_id,
    }


def create_provenance(cnx, provenance):
    if len(provenance) < 1:
        raise ValueError("Provenance list cannot be empty")

    if provenance[0] == "data_center":
        provenance = provenance[1:]

    with cnx.cursor(dictionary=True) as cursor:
        cursor.execute(
            "SELECT UUID AS uuid, DC_UUID AS dc_uuid, DC_CODE AS dc_code FROM data_centers "
            "WHERE DC_UUID = %s",
            (GROUP["uuid"],),
        )
        dc_uuid = cursor.fetchone()
        if dc_uuid is None:
            raise ValueError("Data center not found for provenance creation")

        provenance_items = {
            "data_center": dc_uuid,
        }
        previous_uuid = dc_uuid["uuid"]

        for item in provenance:
            if isinstance(item, dict):
                entity_type = item.pop("entity_type")
            elif isinstance(item, str):
                entity_type = item
            else:
                raise ValueError("Invalid provenance item")

            data = generate_uuid_item()

            entity_type = entity_type.lower()
            if entity_type == "source":
                data["entity_type"] = "SOURCE"
            elif entity_type in ["organ", "block", "section"]:
                data["entity_type"] = "SAMPLE"
            elif entity_type == "dataset":
                data["entity_type"] = "DATASET"
            else:
                raise ValueError(f"Unknown entity type: {entity_type}")

            if isinstance(item, dict):
                data.update(item)

            # Insert the new uuid row
            cursor.execute(
                "INSERT INTO uuids (UUID, ENTITY_TYPE, USER_ID, USER_EMAIL) "
                "VALUES (%s, %s, %s, %s)",
                (
                    data["uuid"],
                    data["entity_type"],
                    data["user_id"],
                    data["user_email"],
                ),
            )

            # Insert the uuid attribute
            cursor.execute(
                "INSERT INTO uuids_attributes (UUID, BASE_ID) VALUES (%s, %s)",
                (
                    data["uuid"],
                    data["base_id"],
                ),
            )

            # Insert the ancestor relationship
            cursor.execute(
                "INSERT INTO ancestors (ANCESTOR_UUID, DESCENDANT_UUID) VALUES (%s, %s)",
                (
                    previous_uuid,
                    data["uuid"],
                ),
            )

            # Retrieve the inserted uuid row
            cursor.execute(
                "SELECT UUID AS uuid, ENTITY_TYPE AS entity_type, "
                "TIME_GENERATED AS time_generated, USER_ID AS user_id, USER_EMAIL AS user_email "
                "FROM uuids WHERE UUID = %s",
                (data["uuid"],),
            )
            inserted = cursor.fetchone()
            if inserted is None:
                raise ValueError("Failed to create provenance item")

            provenance_items[entity_type] = data
            provenance_items[entity_type].update(
                {
                    "uuid": inserted["uuid"],
                    "entity_type": inserted["entity_type"],
                    "time_generated": inserted["time_generated"],
                    "user_id": inserted["user_id"],
                    "user_email": inserted["user_email"],
                }
            )
            previous_uuid = inserted["uuid"]

        cnx.commit()
        return provenance_items


def create_files(cnx, files):
    created_files = []
    for file in files:
        created = create_file(cnx, file)
        created_files.append(created)
    return created_files


def create_file(cnx, file):
    with cnx.cursor(dictionary=True) as cursor:
        data = generate_uuid_item()
        data["entity_type"] = "FILE"

        # Insert the uuid row
        cursor.execute(
            "INSERT INTO uuids (UUID, ENTITY_TYPE, USER_ID, USER_EMAIL) VALUES (%s, %s, %s, %s)",
            (
                data["uuid"],
                data["entity_type"],
                data["user_id"],
                data["user_email"],
            ),
        )

        # Insert the file row
        cursor.execute(
            "INSERT INTO files (UUID, BASE_DIR, PATH, SHA256_CHECKSUM, MD5_CHECKSUM, SIZE) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (
                data["uuid"],
                "DATA_UPLOAD",
                file["path"],
                file["sha256_checksum"],
                file["md5_checksum"],
                file["size"],
            ),
        )

        # Insert the ancestor relationship
        cursor.execute(
            "INSERT INTO ancestors (ANCESTOR_UUID, DESCENDANT_UUID) VALUES (%s, %s)",
            (
                file["parent_uuid"],
                data["uuid"],
            ),
        )
        cnx.commit()

        # Retrieve the inserted file row
        cursor.execute(
            "SELECT files.UUID AS uuid, files.BASE_DIR AS base_dir, files.PATH AS path, "
            "files.SHA256_CHECKSUM AS sha256_checksum, files.MD5_CHECKSUM AS md5_checksum,"
            "files.SIZE AS size, uuids.TIME_GENERATED AS time_generated "
            "FROM files "
            "INNER JOIN uuids ON files.UUID = uuids.UUID "
            "WHERE files.UUID = %s",
            (data["uuid"],),
        )
        inserted = cursor.fetchone()
        if inserted is None:
            raise ValueError("Failed to create file")

        return inserted

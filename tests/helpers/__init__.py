import hashlib

import pytest

GROUP_ID = "7bce0f62-851c-4fdf-afee-5e20581957ba"

GROUP = {
    "name": "EntityAPI-Testing-Group",
    "uuid": GROUP_ID,
    "displayname": "EntityAPI Testing Group",
    "generateuuid": False,
    "data_provider": True,
    "description": "EntityAPI-Testing-Group",
    "tmc_prefix": "TST",
}

USER = {
    "username": "testuser@example.com",
    "name": "Test User",
    "email": "TESTUSER@example.com",
    "sub": "8cb9cda5-1930-493a-8cb9-df6742e0fb42",
    "hmgroupids": [GROUP_ID],
    "group_membership_ids": [GROUP_ID],
    "hmscopes": ["urn:globus:auth:scope:groups.api.globus.org:all"],
}

LAB = {
    "uuid": "3ca38c36e0f04520b3ac32bd7d16d509",
}


@pytest.fixture()
def app(auth, db_session):
    import app as app_module

    app_module.app.config.update({"TESTING": True})
    # other setup
    yield app_module.app
    # cleanup


@pytest.fixture(scope="session", autouse=True)
def clean_up_after_tests():
    """Runs once per pytest session and ensures resources are closed after all tests finish"""
    yield
    # perform cleanup actions here


def calculate_checksum(content, algorithm):
    if algorithm == "md5":
        hasher = hashlib.md5()
    elif algorithm == "sha256":
        hasher = hashlib.sha256()
    else:
        raise ValueError("Unsupported algorithm")

    hasher.update(content.encode("utf-8"))
    return hasher.hexdigest()


CHAR_SET = [
    "B",
    "C",
    "D",
    "F",
    "G",
    "H",
    "J",
    "K",
    "L",
    "M",
    "N",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "V",
    "W",
    "X",
    "Z",
]

NUM_SET = ["2", "3", "4", "5", "6", "7", "8", "9"]

CREATE TABLE hm_uuids
(
  HMUUID VARCHAR(35) PRIMARY KEY,
  DOI_SUFFIX VARCHAR(10) NULL UNIQUE,
  ENTITY_TYPE VARCHAR(20) NOT NULL,
  PARENT_UUID VARCHAR(35) NULL,
  TIME_GENERATED TIMESTAMP NOT NULL,
  USER_ID VARCHAR(50) NOT NULL,
  USER_EMAIL VARCHAR(50) NULL,
  HUBMAP_ID VARCHAR(170) NULL
);

CREATE UNIQUE INDEX UUID_IDX ON hm_uuids (HMUUID);
CREATE UNIQUE INDEX DOI_IDX ON hm_uuids (DOI_SUFFIX);
CREATE UNIQUE INDEX HM_ID_IDX on hm_uuids (HUBMAP_ID);
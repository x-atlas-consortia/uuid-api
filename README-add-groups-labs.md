

### Generate a new LAB uuid
POST to `https://uuid.api.hubmapconsortium.org/uuid` with
```
{
    "entity-type": "LAB"
}
```

```
curl --location --request POST 'https://uuid.api.hubmapconsortium.org/uuid' \
--header 'Authorization: Bearer <token>' \
--header 'Content-Type: application/json' \
--data-raw '{
    "entity_type": "LAB"
}'
```

### Add an entry to UUID_ATTRIBUTES table for it
`insert into uuids_attributes (uuid) values ('<new uuid>');`

### Add an entry to DATA_CENTERS table
`insert into data_centers (uuid, dc_uuid, dc_code) values ('<new uuid>', '<globus group uuid>', '<tmc_prefix>');`

### Add a node to the Neo4j database
`CREATE (n:Lab:Agent {label: '<group name>', uuid: '<globus group uuid>', displayname: '<displayname>', entity_type: 'Lab', created_timestamp: Timestamp(), last_modified_timestamp: Timestamp()})`
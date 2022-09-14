# UUID API Relational Database

The uuid-api service is supported by a MySQL relational database.  The schema of
this database is not unique for any supported project (i.e. HuBMAP and SenNet use the same schema and same service in their
individual deployments.) The files in this directory support the single database model used
by all uuid-api microservices.

## UUID API Relational Database files
The sql directory of the uuid-api Git repository contains these core files:
 * `uuid-api.mwb` is a [MySQL Workbench](https://www.mysql.com/products/workbench/) Model file for maintaining the schema used by uuid-api, and generating the diagram and DDL SQL of the other two files.
 * `uuid-api.pdf` is an Entity-Relationship Diagram for the schema, and is *automatically created from the Model using MySQL Workbench*.
 * `uuid-api.ddl` is a file containing the DDL SQL commands for setting up the schema in an existing database, and is *automatically created from the Model using MySQL Workbench*.

## MySQL Workbench
All aspects of the model (tables, referential integrity constraints, indexes, etc.) are maintained in the Model contained in the `uuid-api.mwb` file.  The Model and MySQL Workbench are generally **_not_** used by the team for database work, but only to generate the following files.

### `uuid-api.pdf` file generation
On the "MySQL Model" tab, double-click the "EER Diagram", if it is not already open.

Save a copy of the Entity-Relationship Diagram using
````
File | Print to File...
````
Save this file as `uuid-api.pdf`.

### `uuid-api.ddl` file generation
The "forward engineer" feature of MySQL Workbench is *partially* executed to generate the DDL SQL commands to populate this file, then cancelled. However, it is also necessary to make a database connection to start "forward engineer" process.
````
Database | Forward Engineer...
````
After setting the connection parameters and clicking "Next", check the following option on the "Options for Database" screen
````
Omit schema qualifier in object names
````
and uncheck the following option on the same screen
````
Generate USE statements
````
Click "Next", and provide the password when prompted.  On the "Select Objects" screen, only check
````
Export MySQL Table Objects
````
Click "Next".  Examine the generated SQL script to assure it is independent of the database it is being executed in. Use the buttons or clipboard to save this file as `uuid-api.ddl`.

Click "Cancel" to abandon the rest of the "forward engineer" process.

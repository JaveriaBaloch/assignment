#!/bin/bash

# Wait for pgAdmin to start
sleep 10

# Create a new server connection in pgAdmin
curl -s -X POST http://admin:admin@localhost:8080/api/servers \
-H "Content-Type: application/json" \
-d '{
      "name": "Postgres Local",
      "group_id": null,
      "hostname": "postgres",
      "port": 5433,
      "username": "myuser",
      "password": "mypassword",
      "ssl_mode": "prefer",
      "maintenance_db": "mydatabase",
      "connect_now": true
    }'

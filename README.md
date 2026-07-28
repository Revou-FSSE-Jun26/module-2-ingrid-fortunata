[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/wGq_UtnU)

# RevoShop API - Backend Development Project

This repository contains the backend code for **RevoShop**, a fictional e-commerce platform. It is being built progressively.

## Checkpoint 1: Database Design

This checkpoint focuses on setting up the initial PostgreSQL database schema and populating it with sample data.

### How to set up the database locally

1. **Install PostgreSQL** (if you haven't already). Ensure you have set a password for the `postgres` superuser.
2. **Create the database**:
   - Open **pgAdmin** or **DBeaver** or use `psql` in your terminal.
   - Create a new database named `revoshop_db`.
     ```sql
     CREATE DATABASE revoshop_db;
     ```
3. **Execute SQL scripts**:
   - Connect to the `revoshop_db` database.
   - Execute the `schema.sql` file first to create all the necessary tables.
   - Execute the `seed.sql` file to populate the tables with sample data.
   - (Optional) Run the queries inside `queries.sql` to verify the data.

### Database Schema Overview

The database consists of 5 tables:

- `users`: Stores user account records.
- `categories`: Product categories.
- `products`: Store items, linked to a category.
- `orders`: Orders placed by a user.
- `order_items`: A junction table linking `orders` and `products` (many-to-many relationship).

#### Database Schema Diagram

![Database Schema Diagram](./img/diagram.png)

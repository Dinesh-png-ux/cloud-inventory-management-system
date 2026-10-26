# Database Schema Documentation

## Project
Cloud-Based Inventory Monitoring and Management System

## Database Technology
SQLite

## 1. Products Table

Purpose: Stores current inventory products and their stock levels.

| Column | Data Type | Description |
|---|---|---|
| id | INTEGER | Primary key; unique product identifier |
| name | TEXT | Product name |
| quantity | INTEGER | Current available stock |
| low_stock_threshold | INTEGER | Stock level used for low-stock alerts |

## 2. Stock Transactions Table

Purpose: Stores stock-in and stock-out records.

| Column | Data Type | Description |
|---|---|---|
| id | INTEGER | Primary key; unique transaction identifier |
| product_id | INTEGER | Related product ID; may be NULL for preserved history |
| transaction_type | TEXT | STOCK_IN or STOCK_OUT |
| quantity | INTEGER | Quantity added or removed |
| created_at | TIMESTAMP | Transaction timestamp |
| product_name | TEXT | Product name preserved for transaction history |

## 3. Table Relationship

A product can have multiple stock transactions.

The stock_transactions.product_id column references products.id.
When a product is deleted, the application sets related transaction product IDs to NULL and preserves the product name so historical records can still be displayed.

## 4. Data Integrity Rules

- Product names must not be empty.
- Duplicate product names are rejected without regard to letter case.
- Stock quantities cannot be negative through the application's stock update workflow.
- Stock Out is rejected when the requested quantity exceeds available stock.
- Transaction records preserve the product name for historical display.

## 5. Database File

File: inventory.db

The database is stored locally during development. Cloud database migration or remote database hosting is not yet completed.

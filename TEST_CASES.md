# Test Cases and Test Results

## Project
Cloud-Based Inventory Monitoring and Management System

## Test Environment
- Operating System: Windows 11 with WSL Ubuntu
- Backend: Python Flask
- Database: SQLite
- Frontend: HTML, CSS and JavaScript

## Test Results

| Test ID | Test Scenario | Expected Result | Actual Result | Status |
|---|---|---|---|---|
| TC-01 | Add a product | Product is added to inventory | Product added successfully | PASS |
| TC-02 | Stock In | Quantity increases | Quantity increased correctly | PASS |
| TC-03 | Stock Out | Quantity decreases | Quantity decreased correctly | PASS |
| TC-04 | Insufficient stock | Stock removal is rejected | Operation rejected; stock unchanged | PASS |
| TC-05 | Duplicate product | Duplicate is rejected | Warning displayed; duplicate not added | PASS |
| TC-06 | Product search | Matching product is displayed | Search worked correctly | PASS |
| TC-07 | Transaction date filter | Matching transactions are displayed | Date filtering worked in tested cases | PASS |
| TC-08 | Application restart | Existing data remains available | Data persisted after restart | PASS |
| TC-09 | Delete product | Product is removed and history preserved | Product removed; history remained | PASS |
| TC-10 | New transaction linkage | Transaction stores product ID and name | Parle transaction stored product ID 2 and name | PASS |

## Notes
- Tests were performed in the local development environment.
- AWS deployment and cloud-specific testing are pending.
- Existing historical transactions with missing product IDs require separate review.

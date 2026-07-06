# StockFlow MVP

## Overview

StockFlow MVP is a SaaS-based Inventory Management System designed to help businesses efficiently manage their inventory. The application provides secure user authentication, organization-based inventory management, dashboard analytics, low-stock monitoring, and product management through a responsive web interface.

The project follows a frontend-backend architecture where the frontend communicates with the backend using REST APIs.

---

# Features

- User Registration and Login
- Secure Authentication
- Organization-based Inventory Management
- Dashboard with Inventory Statistics
- Product Management (Create, Read, Update, Delete)
- Low Stock Monitoring
- Application Settings
- REST API Architecture
- Responsive User Interface
- Cloud Deployment

---

# Technology Stack

## Frontend
- HTML5
- CSS3
- JavaScript

## Backend
- Python

## Database
- SQLite

## Deployment
- Frontend: Vercel
- Backend: Render

## Version Control
- Git & GitHub

---

# Project Structure

```
stockflow-mvp/
│
├── stockflow-split/
│   ├── frontend/
│   └── backend/
│
├── README.md
└── server-error.log
```

---

# Live Deployment

## Frontend

https://stockflow-mvp-k17d.vercel.app

## Backend

https://stockflow-mvp-api-wu6y.onrender.com

## API Base URL

https://stockflow-mvp-api-wu6y.onrender.com/api

## API Health Check

https://stockflow-mvp-api-wu6y.onrender.com/api/health

---

# Installation

## Clone Repository

```bash
git clone https://github.com/Ramesh-Chennamsetty/stockflow-mvp.git
```

## Backend

```bash
cd stockflow-split/backend
pip install -r requirements.txt
python server.py
```

Backend runs at:

```
http://localhost:3000
```

---

## Frontend

```bash
cd stockflow-split/frontend
npm install
npm run dev
```

Frontend runs at:

```
http://localhost:5173
```

---

# Environment Variables

## Frontend

```
VITE_API_URL=https://stockflow-mvp-api-wu6y.onrender.com/api
```

## Backend

```
ENV=production

FRONTEND_URL=https://stockflow-mvp-k17d.vercel.app

DATABASE_PATH=stockflow.db
```

---

# API Documentation

## Base URL

Production

```
https://stockflow-mvp-api-wu6y.onrender.com/api
```

Local Development

```
http://localhost:3000/api
```

---

## API Status

### GET /api

Returns API information.

Example Response

```json
{
  "service": "StockFlow API",
  "status": "OK",
  "message": "Welcome to StockFlow API",
  "health": "/api/health"
}
```

---

## Health Check

### GET /api/health

Example Response

```json
{
  "status": "OK"
}
```

---

## Authentication

### POST /api/signup

Registers a new user.

### POST /api/login

Authenticates a user.

### POST /api/logout

Logs out the current user.

---

## Dashboard

### GET /api/dashboard

Returns dashboard statistics including:

- Total Products
- Total Inventory Quantity
- Low Stock Products

---

## Products

### GET /api/products

Returns all products.

### GET /api/products/{id}

Returns a single product.

### POST /api/products

Creates a new product.

### PUT /api/products/{id}

Updates an existing product.

### DELETE /api/products/{id}

Deletes a product.

---

## Settings

### GET /api/settings

Returns application settings.

### PUT /api/settings

Updates application settings.

---

# HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 404 | Not Found |
| 500 | Internal Server Error |

---

# Security Features

- Secure Authentication
- Organization-based Data Isolation
- RESTful API Design
- Input Validation
- Protected API Endpoints

---

# Future Enhancements

- Barcode Scanner
- Supplier Management
- Purchase Orders
- Sales Reports
- Email Notifications
- CSV Import/Export
- Role-Based Access Control
- Analytics Dashboard
- Cloud Database Support

---

# Author

**Ramesh Chennamsetty**

Email: rameshchennamsetty12@gmail.com

GitHub: https://github.com/Ramesh-Chennamsetty

---

# License

This project is developed for educational and technical assessment purposes.

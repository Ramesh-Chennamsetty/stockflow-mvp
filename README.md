# API Documentation

## Base URL

### Production
```
https://stockflow-mvp-api-wu6y.onrender.com/api
```

### Local Development
```
http://localhost:3000/api
```

---

# Authentication

## Register User

**Endpoint**

```http
POST /signup
```

**Description**

Creates a new organization and administrator account.

**Request Body**

```json
{
  "organizationName": "ABC Store",
  "email": "admin@example.com",
  "password": "Password@123"
}
```

**Success Response**

```json
{
  "success": true,
  "message": "Account created successfully."
}
```

---

## Login

**Endpoint**

```http
POST /login
```

**Description**

Authenticates a registered user.

**Request Body**

```json
{
  "email": "deploy-test-1783073831@example.com",
  "password": "TestPass123!"
}
```

**Success Response**

```json
{
  "success": true,
  "message": "Login successful"
}
```

---

## Logout

**Endpoint**

```http
POST /logout
```

**Description**

Logs out the current user session.

---

# Dashboard

## Get Dashboard Summary

**Endpoint**

```http
GET /dashboard
```

**Description**

Returns the inventory dashboard summary.

**Sample Response**

```json
{
  "totalProducts": 2,
  "totalQuantity": 45,
  "lowStockItems": 5
}
```

---

# Products

## Get All Products

**Endpoint**

```http
GET /products
```

Returns all products belonging to the logged-in organization.

---

## Get Product Details

**Endpoint**

```http
GET /products/{id}
```

Returns details of a specific product.

---

## Add Product

**Endpoint**

```http
POST /products
```

**Request Body**

```json
{
  "name": "Dell Laptop",
  "sku": "DL1001",
  "description": "Dell Inspiron 15",
  "quantity": 15,
  "costPrice": 45000,
  "sellingPrice": 52000,
  "lowStockThreshold": 5
}
```

**Response**

```json
{
  "success": true,
  "message": "Product created successfully."
}
```

---

## Update Product

**Endpoint**

```http
PUT /products/{id}
```

Updates product details.

---

## Delete Product

**Endpoint**

```http
DELETE /products/{id}
```

Deletes the selected product.

---

# Settings

## Get Settings

**Endpoint**

```http
GET /settings
```

Returns application settings.

---

## Update Settings

**Endpoint**

```http
PUT /settings
```

**Request Body**

```json
{
  "defaultLowStockThreshold": 5
}
```

---

# Health Check

## Service Health

**Endpoint**

```http
GET /health
```

**Sample Response**

```json
{
  "service": "StockFlow API",
  "status": "OK",
  "health": "/api/health"
}
```

---

# HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Request completed successfully |
| 201 | Resource created successfully |
| 400 | Bad Request |
| 401 | Unauthorized |
| 404 | Resource Not Found |
| 500 | Internal Server Error |

---

# Security Features

- Secure user authentication
- Organization-based data isolation
- Protected API routes
- Input validation
- RESTful API architecture

---

# Deployment URLs

**Frontend**

```
https://stockflow-mvp-k17d.vercel.app
```

**Backend**

```
https://stockflow-mvp-api-wu6y.onrender.com
```

**API Base URL**

```
https://stockflow-mvp-api-wu6y.onrender.com/api
```

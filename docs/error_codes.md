# API Error Code Reference

Semua error response dari API ini mengikuti format JSON standar:

```json
{
  "error_code": "RESOURCE_ERROR_TYPE",
  "message": "Human-readable description of the error."
}
```

Untuk kegagalan validasi schema payload (HTTP 422), format response menyertakan detail per-field:

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Request body failed validation.",
  "details": {
    "json": {
      "field_name": ["Description of validation rule violation."]
    }
  }
}
```

---

## 1. Global & Framework Error Codes (`app/__init__.py`)

| Error Code | HTTP Status | Pemicu / Deskripsi |
|---|---|---|
| `BAD_REQUEST` | 400 | Format request body rusak / malformed JSON syntax. |
| `NOT_FOUND` | 404 | Endpoint URL / route tidak terdaftar di server. |
| `METHOD_NOT_ALLOWED` | 405 | HTTP method (GET, POST, PUT, dll.) tidak diizinkan pada endpoint tersebut. |
| `VALIDATION_ERROR` | 422 | Payload request gagal validasi schema Marshmallow (tipe data, format, range, atau required field). |
| `INTERNAL_SERVER_ERROR` | 500 | Terjadi unhandled exception / kegagalan server yang tidak terduga. |
| `TOKEN_MISSING` | 401 | Header `Authorization: Bearer <token>` tidak disertakan pada endpoint yang terproteksi JWT. |
| `TOKEN_INVALID` | 401 | JWT token rusak, signature salah, atau format token tidak valid. |
| `TOKEN_EXPIRED` | 401 | JWT token telah melewati masa berlaku (expired). |

---

## 2. Auth & RBAC Authorization (`app/auth.py`, `@roles_required`)

| Error Code | HTTP Status | Pemicu / Deskripsi |
|---|---|---|
| `UNAUTHORIZED` | 401 | JWT token tidak ada, tidak valid, atau user pemegang token tidak ditemukan di database. |
| `FORBIDDEN` | 403 | Akun user berstatus nonaktif (`is_active = false`) atau role user tidak memiliki hak akses ke endpoint. |

---

## 3. Users & Autentikasi (`app/routes/users.py`, `app/validators/user_validators.py`)

| Error Code | HTTP Status | Endpoint | Deskripsi |
|---|---|---|---|
| `USER_NAME_CONFLICT` | 409 | `POST /users`, `PUT /users/<id>` | Username yang dikirim sudah terdaftar pada user lain. |
| `USER_EMAIL_CONFLICT` | 409 | `POST /users`, `PUT /users/<id>` | Email yang dikirim sudah terdaftar pada user lain. |
| `USER_CONFLICT` | 409 | `POST /users`, `PUT /users/<id>` | Terjadi duplikasi username/email pada level constraint database. |
| `USER_NOT_FOUND` | 404 | `GET /users/<id>`, `PUT /users/<id>` | User dengan ID yang diminta tidak ditemukan di database. |
| `USER_FORBIDDEN` | 403 | `GET /users/<id>`, `PUT /users/<id>` | Customer mencoba melihat/mengubah profil user lain, atau mencoba mengubah role/is_active (hanya superadmin). |
| `USER_DEACTIVATED` | 403 | `PUT /users/<id>` | Akun pemohon berstatus nonaktif saat mencoba update data. |
| `USER_UNAUTHORIZED` | 401 | `POST /auth/login` | Kombinasi username/email dan password tidak cocok, atau akun dinonaktifkan. |
| `USER_DATABASE_ERROR` | 500 | `POST /users`, `PUT /users/<id>` | Kesalahan database saat membuat atau memperbarui user. |

---

## 4. Categories (`app/routes/categories.py`, `app/validators/category_validators.py`)

| Error Code | HTTP Status | Endpoint | Deskripsi |
|---|---|---|---|
| `CATEGORY_CONFLICT` | 409 | `POST /categories`, `PUT /categories/<id>` | Nama kategori sudah ada di database (harus unik). |
| `CATEGORY_CONFLICT` | 409 | `DELETE /categories/<id>` | Kategori tidak bisa dihapus karena masih memiliki produk aktif yang terhubung. |
| `CATEGORY_NOT_FOUND` | 404 | `GET /categories/<id>`, `PUT /categories/<id>`, `DELETE /categories/<id>` | Kategori dengan ID yang diminta tidak ditemukan atau tidak aktif (bagi customer). |
| `CATEGORY_DATABASE_ERROR` | 500 | `POST /categories`, `PUT /categories/<id>`, `DELETE /categories/<id>` | Kesalahan database saat create, update, atau delete kategori. |

---

## 5. Products (`app/routes/products.py`, `app/validators/product_validators.py`)

| Error Code | HTTP Status | Endpoint | Deskripsi |
|---|---|---|---|
| `PRODUCT_NOT_FOUND` | 404 | `GET /products/<id>`, `PUT /products/<id>`, `DELETE /products/<id>` | Produk dengan ID yang diminta tidak ditemukan atau tidak aktif (bagi customer). |
| `CATEGORY_NOT_FOUND` | 404 | `POST /products`, `PUT /products/<id>` | `category_id` yang dituju tidak ditemukan di database. |
| `CATEGORY_INACTIVE` | 400 | `POST /products`, `PUT /products/<id>` | Tidak dapat mengaitkan produk ke kategori yang berstatus nonaktif (`is_active = false`). |
| `PRODUCT_CONFLICT` | 409 | `DELETE /products/<id>` | Produk tidak bisa dihapus karena terhubung dengan order yang sedang berjalan (`pending`, `paid`, `processing`, `shipped`). |
| `PRODUCT_DATABASE_ERROR` | 500 | `POST /products`, `PUT /products/<id>`, `DELETE /products/<id>` | Kesalahan database saat create, update, atau delete produk. |

---

## 6. Orders (`app/routes/orders.py`, `app/validators/order_validators.py`)

| Error Code | HTTP Status | Endpoint | Deskripsi |
|---|---|---|---|
| `PRODUCT_NOT_FOUND` | 404 | `POST /orders` | Salah satu produk dalam item order tidak ditemukan atau tidak aktif. |
| `PRODUCT_PRICE_VALIDATION_ERROR` | 400 | `POST /orders` | Harga produk bernilai nol, negatif, atau null. |
| `PRODUCT_STOCK_VALIDATION_ERROR` | 400 | `POST /orders` | Stok produk tidak mencukupi untuk memenuhi kuantitas yang diminta. |
| `ORDER_NOT_FOUND` | 404 | `GET /orders/<id>`, `PATCH /orders/<id>`, `DELETE /orders/<id>` | Order tidak ditemukan, atau customer mencoba mengakses order milik user lain. |
| `ORDER_STATUS_NO_CHANGE` | 409 | `PATCH /orders/<id>` | Order sudah berada pada status yang diminta (no-op update). |
| `ORDER_INVALID_TRANSITION` | 409 | `PATCH /orders/<id>` | Transisi status tidak valid sesuai aturan lifecycle order. |
| `ORDER_FORBIDDEN_TRANSITION` | 403 | `PATCH /orders/<id>` | Customer mencoba melakukan transisi status yang hanya boleh dilakukan admin (misal: `shipped`, `delivered`). |
| `ORDER_CANNOT_BE_CANCELLED` | 409 | `DELETE /orders/<id>` | Order tidak dapat dibatalkan karena sudah masuk status `processing`, `shipped`, `delivered`, atau sudah `cancelled`. |
| `VALIDATION_ERROR` | 422 | `DELETE /orders/<id>` | Alasan pembatalan (`cancellation_reason`) kosong atau tidak disertakan. |
| `ORDER_DATABASE_ERROR` | 500 | `POST /orders`, `PATCH /orders/<id>`, `DELETE /orders/<id>` | Kesalahan database saat membuat, update status, atau membatalkan order. |

---

## 7. Konvensi Penamaan Error Code

```
{RESOURCE}_{ERROR_TYPE}
```

| Bagian | Contoh | Keterangan |
|---|---|---|
| `RESOURCE` | `PRODUCT`, `USER`, `ORDER`, `CATEGORY` | Nama entitas / domain yang menjadi subjek error. |
| `ERROR_TYPE` | `NOT_FOUND`, `CONFLICT`, `VALIDATION_ERROR`, `DATABASE_ERROR`, `FORBIDDEN`, `UNAUTHORIZED` | Kategori masalah teknis atau bisnis yang terjadi. |

### Mapping Error Type ke HTTP Status Code Standar

| Error Type | HTTP Status | Makna RESTful |
|---|---|---|
| `NOT_FOUND` | **404 Not Found** | Resource yang dicari tidak ditemukan di sistem. |
| `CONFLICT` | **409 Conflict** | Terjadi konflik constraint bisnis / database (duplikasi, status transition tidak valid, foreign key lock). |
| `VALIDATION_ERROR` | **400 / 422** | Request body atau parameter melanggar validasi format atau aturan input. |
| `UNAUTHORIZED` | **401 Unauthorized** | Tidak ada token otentikasi atau kredensial salah. |
| `FORBIDDEN` | **403 Forbidden** | Terotentikasi tapi tidak punya wewenang akses (role tidak memadai, akun nonaktif). |
| `DATABASE_ERROR` | **500 Internal Error** | Error tak terduga pada layer database / transaksi SQL. |

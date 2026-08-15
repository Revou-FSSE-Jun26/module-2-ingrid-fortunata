# API Error Code Reference

Semua error response dari API ini mengikuti format JSON berikut:

```json
{
  "error_code": "RESOURCE_ERROR_TYPE",
  "message": "Human-readable description of the error."
}
```

Error code menggunakan format **`RESOURCE_ERROR_TYPE`** (prefix resource + tipe error) agar mudah diidentifikasi dari sisi client.

---

## Auth & Authorization (`app/auth.py`, `@roles_required`)

| Error Code | HTTP Status | Deskripsi |
|---|---|---|
| `UNAUTHORIZED` | 401 | JWT token tidak ada, tidak valid, atau user tidak ditemukan saat verifikasi token. |
| `FORBIDDEN` | 403 | User ditemukan tapi role-nya tidak punya izin mengakses endpoint tersebut, atau akun terdeaktivasi (saat akses resource yang butuh role). |

> Error code ini berasal dari decorator `@roles_required` di `auth.py` dan **tidak** menggunakan prefix resource.

---

## Users (`/users`, `/auth`)

| Error Code | HTTP Status | Endpoint | Deskripsi |
|---|---|---|---|
| `USER_NAME_CONFLICT` | 400 | `POST /users` | Username yang didaftarkan sudah dipakai oleh user lain. |
| `USER_EMAIL_CONFLICT` | 400 | `POST /users` | Email yang didaftarkan sudah dipakai oleh user lain. |
| `USER_CONFLICT` | 400 | `POST /users` | Username atau email duplikat terdeteksi di level database (race condition). |
| `USER_DATABASE_ERROR` | 500 | `POST /users` | Kesalahan tak terduga saat menyimpan user baru ke database. |
| `USER_NOT_FOUND` | 404 | `GET /users/<id>` | User dengan ID yang diminta tidak ditemukan di database. |
| `USER_VALIDATION_ERROR` | 400 | `POST /auth/login` | Field `username`/`email` atau `password` tidak disertakan dalam request login. |
| `USER_UNAUTHORIZED` | 401 | `POST /auth/login` | Kombinasi username/email dan password tidak cocok. |
| `USER_FORBIDDEN` | 403 | `POST /auth/login` | Akun user ditemukan tapi berstatus nonaktif (`is_active = false`). |

---

## Products (`/products`)

| Error Code | HTTP Status | Endpoint | Deskripsi |
|---|---|---|---|
| `PRODUCT_NOT_FOUND` | 404 | `GET /products/<id>`, `PUT /products/<id>`, `DELETE /products/<id>` | Produk dengan ID yang diminta tidak ditemukan atau tidak aktif. |
| `CATEGORY_NOT_FOUND` | 400 | `POST /products`, `PUT /products/<id>` | `category_id` yang dikirim tidak ditemukan di database. |
| `PRODUCT_CONFLICT` | 409 | `DELETE /products/<id>` | Produk tidak bisa dihapus karena masih terhubung dengan data order yang ada. |
| `PRODUCT_DATABASE_ERROR` | 500 | `POST /products`, `PUT /products/<id>`, `DELETE /products/<id>` | Kesalahan tak terduga saat operasi tulis/hapus produk ke database. |

---

## Categories (`/categories`)

| Error Code | HTTP Status | Endpoint | Deskripsi |
|---|---|---|---|
| `CATEGORY_CONFLICT` | 400 | `POST /categories`, `PUT /categories/<id>` | Nama kategori yang dikirim sudah ada di database (harus unik). |
| `CATEGORY_NOT_FOUND` | 404 | `GET /categories/<id>`, `PUT /categories/<id>`, `DELETE /categories/<id>` | Kategori dengan ID yang diminta tidak ditemukan di database. |
| `CATEGORY_DATABASE_ERROR` | 500 | `POST /categories`, `PUT /categories/<id>`, `DELETE /categories/<id>` | Kesalahan tak terduga saat operasi tulis/hapus kategori ke database. |

---

## Orders (`/orders`)

| Error Code | HTTP Status | Endpoint | Deskripsi |
|---|---|---|---|
| `ORDER_VALIDATION_ERROR` | 400 | `POST /orders` | Request tidak valid: tidak ada item dalam order, atau quantity item nol/negatif. |
| `PRODUCT_NOT_FOUND` | 404 | `POST /orders` | Salah satu produk dalam order tidak ditemukan atau tidak aktif. |
| `PRODUCT_PRICE_VALIDATION_ERROR` | 400 | `POST /orders` | Harga produk bernilai nol, negatif, atau null — tidak bisa dijadikan dasar transaksi. |
| `PRODUCT_STOCK_VALIDATION_ERROR` | 400 | `POST /orders` | Stok produk tidak mencukupi untuk memenuhi jumlah yang diminta. |
| `ORDER_DATABASE_ERROR` | 500 | `POST /orders`, `DELETE /orders/<id>` | Kesalahan tak terduga saat membuat atau menghapus order di database. |
| `USER_NOT_FOUND` | 401 | `GET /orders`, `GET /orders/<id>`, `DELETE /orders/<id>` | User yang teridentifikasi dari JWT token tidak ditemukan di database. |
| `ORDER_NOT_FOUND` | 404 | `GET /orders/<id>`, `DELETE /orders/<id>` | Order dengan ID yang diminta tidak ditemukan, atau user tidak punya akses ke order tersebut. |

---

## Konvensi Penamaan Error Code

```
{RESOURCE}_{ERROR_TYPE}
```

| Bagian | Contoh | Keterangan |
|---|---|---|
| `RESOURCE` | `PRODUCT`, `USER`, `ORDER`, `CATEGORY` | Resource yang menjadi sumber error |
| `ERROR_TYPE` | `NOT_FOUND`, `CONFLICT`, `DATABASE_ERROR`, `VALIDATION_ERROR` | Jenis kesalahan yang terjadi |

### Jenis Error Type

| Error Type | Biasanya HTTP | Artinya |
|---|---|---|
| `NOT_FOUND` | 404 | Resource tidak ditemukan |
| `CONFLICT` | 409 | Duplikat data atau constraint dilanggar |
| `VALIDATION_ERROR` | 400 | Input dari client tidak valid |
| `DATABASE_ERROR` | 500 | Error tak terduga di level database |
| `UNAUTHORIZED` | 401 | Kredensial tidak valid |
| `FORBIDDEN` | 403 | Akses ditolak (role/status tidak sesuai) |

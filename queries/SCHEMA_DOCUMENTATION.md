# Dokumentasi Desain Basis Data RevoFashion API (`schema.sql`)

Dokumen ini menjelaskan rancangan skema basis data PostgreSQL untuk platform e-commerce fashion **RevoFashion** (terinspirasi dari Uniqlo), beserta filosofi keputusan desain integritas data, tipe data, dan aturan referensial (*Foreign Key Constraints*).

---

## 📌 Overview Rancangan Skema

Skema basis data RevoFashion terdiri dari 6 tabel utama yang saling terhubung:

```
[users] (1) <--- (N) [orders] (1) <--- (N) [order_items] (N) ---> (1) [products] (N) ---> (1) [categories]
                                                                         |
                                                                    [product_images]
```

1. **`users`**: Menyimpan akun pengguna (pembeli/pelanggan) dengan role-based access.
2. **`categories`**: Mengelompokkan jenis produk fashion (T-Shirts, Outerwear, Pants & Jeans, dll).
3. **`products`**: Katalog pakaian yang dijual, dengan atribut fashion seperti `size`, `color`, `material`, `gender`, dan `sku`.
4. **`product_images`**: Gambar produk (base64), mendukung hingga 3 gambar per produk dengan 1 gambar utama.
5. **`orders`**: Transaksi belanja yang dibuat oleh `users`.
6. **`order_items`**: Tabel perantara (*junction table*) antara `orders` dan `products` untuk mendukung hubungan *many-to-many* beserta harga historis, ukuran, dan warna pada saat pembelian.

---

## 👗 Atribut Fashion pada Tabel `products`

| Kolom | Tipe | Keterangan |
| :--- | :--- | :--- |
| `size` | `VARCHAR(20)` | Ukuran pakaian: XS, S, M, L, XL, XXL, FREE |
| `color` | `VARCHAR(50)` | Nama warna (contoh: "Navy", "Off White", "Olive") |
| `material` | `VARCHAR(150)` | Bahan kain (contoh: "100% Cotton", "58% Cotton, 38% Polyester, 4% Spandex") |
| `gender` | `VARCHAR(20)` | Target gender: Men, Women, Unisex, Kids |
| `sku` | `VARCHAR(50) UNIQUE` | Kode Stock Keeping Unit yang unik per produk |

### Filosofi: Satu baris = Satu varian

Setiap kombinasi ukuran/warna produk disimpan sebagai baris terpisah, mirip dengan cara Uniqlo mengelola inventaris per SKU. Contoh:
- AIRism T-Shirt White (M) → SKU: `RF-TS-001`
- AIRism T-Shirt White (L) → SKU: `RF-TS-001-L` (jika ditambahkan)

---

## 👕 Atribut Fashion pada Tabel `order_items`

| Kolom | Tipe | Keterangan |
| :--- | :--- | :--- |
| `size` | `VARCHAR(20)` | Ukuran yang dipilih pelanggan saat pembelian |
| `color` | `VARCHAR(50)` | Warna yang dipilih pelanggan saat pembelian |

Kolom ini menyimpan snapshot ukuran dan warna pada saat order dibuat, sehingga jika produk diubah di masa depan, data pada nota pesanan lama tetap akurat.

---

## 🛠️ Keputusan Desain & Perlakuan `ON DELETE` Constraint

Keamanan data transaksi (*Audit Trail*) adalah prioritas utama dalam sistem e-commerce. Oleh karena itu, kita memilih aturan penghapusan data (*referential action*) yang aman:

| Foreign Key | Relasi | Aturan `ON DELETE` | Alasan & Analisis Keamanan |
| :--- | :--- | :--- | :--- |
| `orders.user_id` | `orders` ➔ `users` | **`RESTRICT`** | **Mencegah Hilangnya Data Keuangan.** Jika user dihapus, perintah dihapus akan **ditolak (error)** jika user tsb memiliki riwayat transaksi. Ini menjaga laporan penjualan dan bukti audit keuangan tetap utuh. |
| `order_items.order_id` | `order_items` ➔ `orders` | **`RESTRICT`** | **Melindungi Detail Transaksi.** Menghindari penghapusan otomatis rincian item belanjaan demi keamanan jejak histori. |
| `order_items.product_id` | `order_items` ➔ `products` | **`RESTRICT`** | **Mencegah Kerusakan Histori Pembelian.** Produk yang pernah dibeli oleh pelanggan tidak boleh dihapus dari database karena akan merusak invoice/nota belanjaan lama. |
| `products.category_id` | `products` ➔ `categories` | **`SET NULL`** | **Katalog Tetap Fleksibel.** Jika sebuah kategori dihapus, produk di dalamnya tidak ikut terhapus, melainkan nilai `category_id` berubah menjadi `NULL` (*Uncategorized*). |
| `product_images.product_id` | `product_images` ➔ `products` | **`CASCADE`** | **Gambar Terikat Produk.** Jika produk dihapus, gambar-gambar terkait juga dihapus secara otomatis. |

### ⚠️ Mengapa `ON DELETE CASCADE` Dihindari/Dianggap Berbahaya?

1. **Risiko Efek Domino (*Cascade Delete*)**  
   Penggunaan `ON DELETE CASCADE` pada relasi penting seperti `users` ➔ `orders` berarti jika satu baris `user` dihapus via `DELETE FROM users WHERE id = X;`, secara otomatis **seluruh pesanan (`orders`) dan rincian belanjaan (`order_items`) milik user tersebut akan terhapus permanen dari database**.
2. **Kehilangan Jejak Financial / Laporan Bisnis**  
   Dalam dunia industri nyata, penghapusan data transaksi berakibat fatal pada laporan akuntansi, pajak, dan audit hukum perusahaan.
3. **Praktik Terbaik Industri (*Soft Delete*)**  
   Sistem modern tidak melakukan penghapusan fisik (*Hard Delete*), melainkan menggunakan *Soft Delete* (misal penandaan kolom `is_active = false` atau `deleted_at`).

---

## 📋 Rincian Aturan Validasi & Constraint Lainnya

Selain *Foreign Key*, setiap tabel dilengkapi dengan validasi di tingkat basis data (*Database-Level Constraints*) untuk menjamin konsistensi data:

### 1. Tabel `users`
- `username`: Harus unik (`UNIQUE`) dan minimal 3 karakter (`CHECK (length(username) >= 3)`).
- `email`: Harus unik (`UNIQUE`) dan memiliki format email valid yang mengandung karakter `@` (`CHECK (email LIKE '%@%')`).
- `role`: Role pengguna — `superadmin`, `admin`, atau `customer`.

### 2. Tabel `categories`
- `name`: Harus unik (`UNIQUE`) agar tidak ada kategori ganda.
- Contoh kategori fashion: T-Shirts, Shirts & Blouses, Pants & Jeans, Outerwear, Dresses & Skirts, Activewear, Innerwear & Loungewear.

### 3. Tabel `products`
- `price`: Tidak boleh bernilai negatif (`CHECK (price >= 0)`).
- `stock`: Tidak boleh negatif dan memiliki nilai default 0 (`CHECK (stock >= 0)`).
- `sku`: Kode unik per varian produk (`UNIQUE`).
- `size`: Ukuran pakaian (validasi di level aplikasi: XS, S, M, L, XL, XXL, FREE).
- `gender`: Target gender (validasi di level aplikasi: Men, Women, Unisex, Kids).

### 4. Tabel `orders`
- `total_amount`: Total belanjaan tidak boleh negatif (`CHECK (total_amount >= 0)`).
- `status`: Dibatasi hanya pada status valid yang diizinkan (`CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled'))`).

### 5. Tabel `order_items`
- `PRIMARY KEY (order_id, product_id)`: Memastikan satu item produk hanya muncul satu kali dalam satu order yang sama.
- `quantity`: Jumlah barang yang dibeli harus lebih dari 0 (`CHECK (quantity > 0)`).
- `price_at_purchase`: Menyimpan harga produk pada saat pesanan dibuat.
- `size`: Menyimpan ukuran yang dipilih saat pesanan dibuat.
- `color`: Menyimpan warna yang dipilih saat pesanan dibuat.

# Dokumentasi Desain Basis Data RevoShop API (`schema.sql`)

Dokumen ini menjelaskan rancangan skema basis data PostgreSQL untuk platform e-commerce **RevoShop**, beserta filosofi keputusan desain integritas data, tipe data, dan aturan referensial (*Foreign Key Constraints*).

---

## 📌 Overview Rancangan Skema

Skema basis data RevoShop terdiri dari 5 tabel utama yang saling terhubung:

```
[users] (1) <--- (N) [orders] (1) <--- (N) [order_items] (N) ---> (1) [products] (N) ---> (1) [categories]
```

1. **`users`**: Menyimpan akun pengguna (pembeli/pelanggan).
2. **`categories`**: Mengelompokkan jenis produk.
3. **`products`**: Katalog barang yang dijual, terhubung ke `categories`.
4. **`orders`**: Transaksi belanja yang dibuat oleh `users`.
5. **`order_items`**: Tabel perantara (*junction table*) antara `orders` dan `products` untuk mendukung hubungan *many-to-many* beserta harga historis pembelian (`price_at_purchase`).

---

## 🛠️ Keputusan Desain & Perlakuan `ON DELETE` Constraint

Keamanan data transaksi (*Audit Trail*) adalah prioritas utama dalam sistem e-commerce. Oleh karena itu, kita memilih aturan penghapusan data (*referential action*) yang aman:

| Foreign Key | Relasi | Aturan `ON DELETE` | Alasan & Analisis Keamanan |
| :--- | :--- | :--- | :--- |
| `orders.user_id` | `orders` ➔ `users` | **`RESTRICT`** | **Mencegah Hilangnya Data Keuangan.** Jika user dihapus, perintah dihapus akan **ditolak (error)** jika user tsb memiliki riwayat transaksi. Ini menjaga laporan penjualan dan bukti audit keuangan tetap utuh. |
| `order_items.order_id` | `order_items` ➔ `orders` | **`RESTRICT`** | **Melindungi Detail Transaksi.** Menghindari penghapusan otomatis rincian item belanjaan demi keamanan jejak histori. |
| `order_items.product_id` | `order_items` ➔ `products` | **`RESTRICT`** | **Mencegah Kerusakan Histori Pembelian.** Produk yang pernah dibeli oleh pelanggan tidak boleh dihapus dari database karena akan merusak invoice/nota belanjaan lama. |
| `products.category_id` | `products` ➔ `categories` | **`SET NULL`** | **Katalog Tetap Fleksibel.** Jika sebuah kategori dihapus, produk di dalamnya tidak ikut terhapus, melainkan nilai `category_id` berubah menjadi `NULL` (*Uncategorized*). |

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

### 2. Tabel `categories`
- `name`: Harus unik (`UNIQUE`) agar tidak ada kategori ganda.

### 3. Tabel `products`
- `price`: Tidak boleh bernilai negatif (`CHECK (price >= 0)`).
- `stock`: Tidak boleh negatif dan memiliki nilai default 0 (`CHECK (stock >= 0)`).

### 4. Tabel `orders`
- `total_amount`: Total belanjaan tidak boleh negatif (`CHECK (total_amount >= 0)`).
- `status`: Dibatasi hanya pada status valid yang diizinkan (`CHECK (status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled'))`).

### 5. Tabel `order_items`
- `PRIMARY KEY (order_id, product_id)`: Memastikan satu item produk hanya muncul satu kali dalam satu order yang sama.
- `quantity`: Jumlah barang yang dibeli harus lebih dari 0 (`CHECK (quantity > 0)`).
- `price_at_purchase`: Menyimpan harga produk pada saat pesanan dibuat. Hal ini penting agar jika harga di tabel `products` berubah di masa depan, nilai pada nota pesanan lama tidak ikut berubah.

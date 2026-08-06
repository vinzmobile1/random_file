import streamlit as st
import pandas as pd

st.set_page_config(page_title="Kalkulator Harga Tampil", layout="wide")

# --- FORMATTING FUNCTIONS ---
def format_rp(angka):
    return f"Rp {int(round(angka)):,.0f}".replace(",", ".")

def format_pct(angka):
    return f"{angka:.2f}%"

# --- INIT STATE: TABEL DINAMIS DEFAULT ---
# Membuat default data seperti gambar agar user tidak perlu repot input dari nol
if 'biaya_df' not in st.session_state:
    st.session_state.biaya_df = pd.DataFrame([
        {"Aktif": True, "Deskripsi": "Biaya Administrasi", "Kategori": "Admin", "Tipe Cut": "Persentase (%)", "Nilai": 4.7, "Max (Rp)": 0},
        {"Aktif": True, "Deskripsi": "Gratis Ongkir XTRA (1% - Max 40rb)", "Kategori": "Layanan", "Tipe Cut": "Persen dgn Batas Max", "Nilai": 1.0, "Max (Rp)": 40000},
        {"Aktif": True, "Deskripsi": "Layanan Mall 1.8% - Max 50rb", "Kategori": "Layanan", "Tipe Cut": "Persen dgn Batas Max", "Nilai": 1.8, "Max (Rp)": 50000},
        {"Aktif": True, "Deskripsi": "Promo XTRA+ (6.5%) 80rb", "Kategori": "Layanan", "Tipe Cut": "Persen dgn Batas Max", "Nilai": 6.5, "Max (Rp)": 80000},
        {"Aktif": True, "Deskripsi": "Biaya Proses Pesanan", "Kategori": "Layanan", "Tipe Cut": "Nominal (Rp)", "Nilai": 1250.0, "Max (Rp)": 0},
        {"Aktif": True, "Deskripsi": "Biaya Asuransi 0,5%", "Kategori": "Asuransi", "Tipe Cut": "Persentase (%)", "Nilai": 0.5, "Max (Rp)": 0},
    ])


# --- CORE LOGIC CALCULATION ---
def calculate_shopee(harga_tampil, target_bersih, voucher_cfg, fees_df):
    A = harga_tampil
    
    # 1. VOUCHER
    if voucher_cfg['use']:
        B = min(A * (voucher_cfg['pct']/100), voucher_cfg['max_rp'])
        C = B * (voucher_cfg['seller_pct']/100)
    else:
        B, C = 0, 0
        
    D = A - B
    if D <= 0: return 0, [], 0, 0
    
    # 2. BIAYA LAYANAN DARI TABEL DINAMIS
    admin_total = 0
    layanan_total = 0
    asuransi_total = 0
    rincian_potongan = []
    
    for idx, row in fees_df.iterrows():
        if not row["Aktif"]:
            rincian_potongan.append(0)
            continue
            
        val = 0
        if row["Tipe Cut"] == "Persentase (%)":
            val = D * (row["Nilai"] / 100)
        elif row["Tipe Cut"] == "Persen dgn Batas Max":
            val = min(D * (row["Nilai"] / 100), row["Max (Rp)"])
        elif row["Tipe Cut"] == "Nominal (Rp)":
            val = row["Nilai"]
            
        val = round(val)
        rincian_potongan.append(val)
        
        # Kelompokkan berdasarkan kategori untuk perhitungan utang selisih Shopee
        if row["Kategori"] == "Admin": admin_total += val
        elif row["Kategori"] == "Layanan": layanan_total += val
        elif row["Kategori"] == "Asuransi": asuransi_total += val

    # 3. LOGIC UTANG FEE & SUBSIDI (Sesuai rumus lama)
    M = B - C
    N = admin_total / D if D > 0 else 0
    O = layanan_total / D if D > 0 else 0
    
    P = round(N * M)
    Q = round(O * M)
    R = P + Q
    
    S = M - R
    T = D - asuransi_total - admin_total - layanan_total
    
    U = S + T # Harga Bersih (Pendapatan Akhir)
    
    return U, rincian_potongan, (admin_total + layanan_total + asuransi_total), D

def find_optimum_price(target_bersih, voucher_cfg, fees_df):
    low = target_bersih
    high = target_bersih * 3.0 
    
    # Binary search real-time
    for _ in range(70): 
        mid = (low + high) / 2
        current_bersih, _, _, _ = calculate_shopee(mid, target_bersih, voucher_cfg, fees_df)
        if current_bersih < target_bersih:
            low = mid
        else:
            high = mid
            
    final_harga = round(high)
    _, rincian, total_potongan, hrg_stlh_voc = calculate_shopee(final_harga, target_bersih, voucher_cfg, fees_df)
    return final_harga, rincian, total_potongan, hrg_stlh_voc


# --- USER INTERFACE (UI) ---
st.title("📊 Kalkulator Harga Jual Optimum (Real-Time)")
st.markdown("Ubah angka di bawah ini, perhitungan akan berjalan otomatis tanpa perlu klik tombol.")

# 1. INPUT TARGET & VOUCHER
col1, col2 = st.columns(2)
with col1:
    st.subheader("💰 Target Pendapatan")
    target_bersih = st.number_input("Harga Bersih yang diinginkan (Rp):", min_value=1000, value=7150522, step=10000)

with col2:
    st.subheader("🎟️ Pengaturan Voucher")
    use_voucher = st.checkbox("Gunakan Voucher Diskon", value=True)
    
    if use_voucher:
        c1, c2 = st.columns(2)
        with c1:
            v_pct = st.number_input("% Voucher", value=30.0, step=1.0)
            v_max = st.number_input("Max Voucher (Rp)", value=500000, step=10000)
        with c2:
            v_shopee_pct = st.number_input("% Ditanggung Shopee", value=65.0, step=1.0)
            v_seller_pct = st.number_input("% Ditanggung Seller", value=35.0, step=1.0)
    else:
        v_pct, v_max, v_shopee_pct, v_seller_pct = 0, 0, 0, 0

voucher_cfg = {
    'use': use_voucher, 'pct': v_pct, 'max_rp': v_max, 
    'shopee_pct': v_shopee_pct, 'seller_pct': v_seller_pct
}

# 2. TABEL BIAYA (Bisa di Edit / Tambah Baris)
st.markdown("---")
st.subheader("⚙️ Rincian Biaya & Komponen (Tabel Dinamis)")
st.info("💡 Anda bisa mengedit angka, mencentang/uncentang komponen, hingga **menambah/menghapus baris** secara langsung pada tabel di bawah.")

# Konfigurasi kolom tabel agar ramah pengguna
config_kolom = {
    "Aktif": st.column_config.CheckboxColumn("Status", default=True),
    "Deskripsi": st.column_config.TextColumn("Deskripsi Biaya / Komponen"),
    "Kategori": st.column_config.SelectboxColumn("Kategori (Penting untuk Rumus)", options=["Admin", "Layanan", "Asuransi"], required=True),
    "Tipe Cut": st.column_config.SelectboxColumn("Tipe Potongan", options=["Persentase (%)", "Persen dgn Batas Max", "Nominal (Rp)"], required=True),
    "Nilai": st.column_config.NumberColumn("Nilai (% atau Rp)"),
    "Max (Rp)": st.column_config.NumberColumn("Batas Max (Rp)"),
}

# Render data editor (User input)
edited_df = st.data_editor(
    st.session_state.biaya_df, 
    column_config=config_kolom, 
    num_rows="dynamic", # Memungkinkan fitur tambah/hapus baris
    use_container_width=True,
    hide_index=True
)

# 3. KALKULASI & HASIL (Menyatu dalam UI)
harga_optimum, rincian_potongan, total_potongan, hrg_stlh_voc = find_optimum_price(target_bersih, voucher_cfg, edited_df)

# Merangkai kembali tabel dengan tambahan kolom "Nominal Potongan" dari hasil hitung
output_df = edited_df.copy()
output_df["Nominal Potongan"] = [format_rp(x) if aktif else "-" for x, aktif in zip(rincian_potongan, edited_df["Aktif"])]

# TAMPILAN BANNER HASIL UTAMA (Menyerupai Gambar)
st.markdown("---")
pct_total_potongan = (total_potongan / hrg_stlh_voc * 100) if hrg_stlh_voc > 0 else 0

st.markdown(f"""
<div style="background-color: #f0f8ff; padding: 20px; border-radius: 10px; border: 1px solid #cce0ff; display: flex; justify_content: space-between; align-items: center;">
    <div>
        <h3 style="color: #0044cc; margin: 0;">📊 KALKULASI HARGA JUAL OPTIMUM</h3>
    </div>
    <div style="text-align: right;">
        <h1 style="color: #0055ff; margin: 0; font-size: 36px;">{format_rp(harga_optimum)}</h1>
        <span style="background-color: white; padding: 5px 15px; border-radius: 20px; border: 1px solid #ccc; font-size: 14px;">
            Total Potongan: <b>{format_pct(pct_total_potongan)}</b> / {format_rp(total_potongan)}
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# TAMPILAN TABEL FINAL DENGAN NOMINAL POTONGAN
st.write("#### Rekap Nominal Potongan per Komponen")
st.dataframe(
    output_df[["Aktif", "Deskripsi", "Tipe Cut", "Nilai", "Max (Rp)", "Nominal Potongan"]],
    use_container_width=True,
    hide_index=True
)

st.caption("✅ Harga bersih setelah semua potongan dipastikan sesuai dengan Target Pendapatan Anda.")

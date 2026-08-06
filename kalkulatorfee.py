import streamlit as st
import pandas as pd

st.set_page_config(page_title="Kalkulator Harga Tampil", layout="wide")

# --- FORMATTING FUNCTIONS ---
def format_rp(angka):
    return f"Rp {int(round(angka)):,.0f}".replace(",", ".")

# --- INIT STATE: TABEL DATA MENTAH ---
# Menyimpan data tabel (tanpa kolom hasil hitung) di session state
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
    
    if voucher_cfg['use']:
        B = min(A * (voucher_cfg['pct']/100), voucher_cfg['max_rp'])
        C = B * (voucher_cfg['seller_pct']/100)
    else:
        B, C = 0, 0
        
    D = A - B
    if D <= 0: return 0, [], 0, 0
    
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
        
        if row["Kategori"] == "Admin": admin_total += val
        elif row["Kategori"] == "Layanan": layanan_total += val
        elif row["Kategori"] == "Asuransi": asuransi_total += val

    M = B - C
    N = admin_total / D if D > 0 else 0
    O = layanan_total / D if D > 0 else 0
    
    P = round(N * M)
    Q = round(O * M)
    R = P + Q
    
    S = M - R
    T = D - asuransi_total - admin_total - layanan_total
    
    U = S + T
    
    return U, rincian_potongan, (admin_total + layanan_total + asuransi_total), D

def find_optimum_price(target_bersih, voucher_cfg, fees_df):
    low = target_bersih
    high = target_bersih * 3.0 
    
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
st.title("🍊 Kalkulator Harga Jual Shopee (Tabel Tunggal)")

# 1. INPUT TARGET & VOUCHER
col1, col2 = st.columns(2)
with col1:
    st.subheader("💰 Target Pendapatan")
    target_bersih = st.number_input("Harga Bersih (Pencairan) yang diinginkan:", min_value=1000, value=7150522, step=10000)

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

# --- HITUNG BERDASARKAN DATA SAAT INI ---
harga_optimum, rincian_potongan, total_potongan, hrg_stlh_voc = find_optimum_price(
    target_bersih, voucher_cfg, st.session_state.biaya_df
)

# 2. MENAMPILKAN HARGA FINAL DI ATAS TABEL
st.markdown("---")
pct_total_potongan = (total_potongan / hrg_stlh_voc * 100) if hrg_stlh_voc > 0 else 0

c_res1, c_res2 = st.columns([1, 1])
c_res1.metric(label="🎯 Harga Jual Optimum (Harga Tampil)", value=format_rp(harga_optimum))
c_res2.metric(label="📉 Total Potongan Biaya & Asuransi", value=format_rp(total_potongan), delta=f"-{pct_total_potongan:.2f}%", delta_color="inverse")

# 3. TABEL DINAMIS (INPUT + OUTPUT GABUNGAN)
st.subheader("⚙️ Rincian Biaya & Komponen")

# Membuat salinan dataframe khusus untuk ditampilkan di layar (menambahkan kolom hasil hitung)
display_df = st.session_state.biaya_df.copy()
display_df["Nominal Potongan"] = [f"- {format_rp(x)}" if aktif else "-" for x, aktif in zip(rincian_potongan, display_df["Aktif"])]

# Konfigurasi kolom
config_kolom = {
    "Aktif": st.column_config.CheckboxColumn("Status", default=True),
    "Deskripsi": st.column_config.TextColumn("Deskripsi Biaya / Komponen"),
    "Kategori": st.column_config.SelectboxColumn("Kategori (Wajib)", options=["Admin", "Layanan", "Asuransi"], required=True),
    "Tipe Cut": st.column_config.SelectboxColumn("Tipe Potongan", options=["Persentase (%)", "Persen dgn Batas Max", "Nominal (Rp)"], required=True),
    "Nilai": st.column_config.NumberColumn("Nilai (%/Rp)", format="%.2f"),
    "Max (Rp)": st.column_config.NumberColumn("Batas Max (Rp)", format="%d"),
    "Nominal Potongan": st.column_config.TextColumn("Nominal Potongan (Otomatis)", disabled=True) # DISABLED = READ-ONLY
}

# Render tabel
edited_df = st.data_editor(
    display_df, 
    column_config=config_kolom, 
    num_rows="dynamic", # Bisa tambah/hapus baris
    use_container_width=True,
    hide_index=True
)

# Cek apakah user merubah isi tabel (merubah angka, centang, tambah/hapus baris)
# Jika berubah, simpan perubahannya ke session state, lalu muat ulang halaman agar angka terhitung ulang
new_state_df = edited_df.drop(columns=["Nominal Potongan"]).reset_index(drop=True)
if not new_state_df.equals(st.session_state.biaya_df.reset_index(drop=True)):
    st.session_state.biaya_df = new_state_df
    st.rerun()

st.caption("💡 *Tabel di atas sepenuhnya interaktif. Anda bisa mengedit nilai, mencentang/menghapus centang (Status), hingga menambah baris baru. Hasil akan langsung terhitung ulang seketika pada kolom paling kanan (Nominal Potongan).*")

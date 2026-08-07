import streamlit as st
import pandas as pd

st.set_page_config(page_title="Kalkulator Harga Jual Shopee", layout="wide")

# --- FORMATTING FUNCTIONS ---
def format_rp(angka):
    return f"Rp {int(round(angka)):,.0f}".replace(",", ".")

def format_pct(angka):
    return f"{angka * 100:.2f}%"

# --- INIT STATE: TABEL DATA MENTAH ---
if 'biaya_df' not in st.session_state:
    st.session_state.biaya_df = pd.DataFrame([
        {"Aktif": True, "Deskripsi": "Biaya Administrasi", "Kategori": "Admin", "Tipe Cut": "Persentase (%)", "Persentase (%)": 4.7, "Nominal / Batas Max (Rp)": 0},
        {"Aktif": True, "Deskripsi": "Gratis Ongkir XTRA (1% - Max 40rb)", "Kategori": "Layanan", "Tipe Cut": "Persen dgn Batas Max", "Persentase (%)": 1.0, "Nominal / Batas Max (Rp)": 40000},
        {"Aktif": True, "Deskripsi": "Layanan Mall 1.8% - Max 50rb", "Kategori": "Layanan", "Tipe Cut": "Persen dgn Batas Max", "Persentase (%)": 1.8, "Nominal / Batas Max (Rp)": 50000},
        {"Aktif": True, "Deskripsi": "Promo XTRA+ (6.5%) 80rb", "Kategori": "Layanan", "Tipe Cut": "Persen dgn Batas Max", "Persentase (%)": 6.5, "Nominal / Batas Max (Rp)": 80000},
        {"Aktif": True, "Deskripsi": "Biaya Proses Pesanan", "Kategori": "Layanan", "Tipe Cut": "Nominal (Rp)", "Persentase (%)": 0.0, "Nominal / Batas Max (Rp)": 1250},
        {"Aktif": True, "Deskripsi": "Biaya Asuransi 0,5%", "Kategori": "Asuransi", "Tipe Cut": "Persentase (%)", "Persentase (%)": 0.5, "Nominal / Batas Max (Rp)": 0},
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
    
    if D <= 0: 
        return 0, [], 0, 0, {}
    
    admin_total = 0
    layanan_total = 0
    asuransi_total = 0
    rincian_potongan = []
    
    for idx, row in fees_df.iterrows():
        # CEK NILAI KOSONG (NONE/NAN) SAAT BARIS BARU DITAMBAHKAN
        is_aktif = row["Aktif"] if pd.notna(row["Aktif"]) else False
        
        if not is_aktif:
            rincian_potongan.append(0)
            continue
            
        # Ubah nilai None menjadi 0 atau string default agar tidak TypeError
        pct_val = float(row["Persentase (%)"]) if pd.notna(row["Persentase (%)"]) else 0.0
        nom_val = float(row["Nominal / Batas Max (Rp)"]) if pd.notna(row["Nominal / Batas Max (Rp)"]) else 0.0
        tipe_cut = str(row["Tipe Cut"]) if pd.notna(row["Tipe Cut"]) else "Persentase (%)"
        kategori = str(row["Kategori"]) if pd.notna(row["Kategori"]) else "Layanan"
        
        val = 0
        
        # LOGIC PERUBAHAN TIPE CUT
        if tipe_cut == "Persentase (%)":
            val = D * (pct_val / 100)
        elif tipe_cut == "Persen dgn Batas Max":
            val = min(D * (pct_val / 100), nom_val)
        elif tipe_cut == "Nominal (Rp)":
            val = nom_val 
            
        val = round(val)
        rincian_potongan.append(val)
        
        if kategori == "Admin": admin_total += val
        elif kategori == "Layanan": layanan_total += val
        elif kategori == "Asuransi": asuransi_total += val

    M = B - C
    N = admin_total / D if D > 0 else 0
    O = layanan_total / D if D > 0 else 0
    
    P = round(N * M)
    Q = round(O * M)
    R = P + Q
    
    S = M - R
    T = D - asuransi_total - admin_total - layanan_total
    
    U = S + T
    
    # Simpan semua rincian logika ke dictionary untuk tabel Summary
    breakdown = {
        'Harga Tampil': A, 'D': D, 'Admin': admin_total, 'Layanan': layanan_total, 'Asuransi': asuransi_total,
        'M': M, 'N': N, 'O': O, 'P': P, 'Q': Q, 'R': R, 'S': S, 'T': T, 'U': U
    }
    
    return U, rincian_potongan, (admin_total + layanan_total + asuransi_total), D, breakdown

def find_optimum_price(target_bersih, voucher_cfg, fees_df):
    low = target_bersih
    high = target_bersih * 3.0 
    
    for _ in range(70): 
        mid = (low + high) / 2
        current_bersih, _, _, _, _ = calculate_shopee(mid, target_bersih, voucher_cfg, fees_df)
        if current_bersih < target_bersih:
            low = mid
        else:
            high = mid
            
    final_harga = round(high)
    _, rincian, total_potongan, hrg_stlh_voc, breakdown = calculate_shopee(final_harga, target_bersih, voucher_cfg, fees_df)
    return final_harga, rincian, total_potongan, hrg_stlh_voc, breakdown


# --- USER INTERFACE (UI) ---
st.title("🍊 Kalkulator Harga Jual Shopee")

# 1. INPUT TARGET & VOUCHER
col1, col2 = st.columns(2)
with col1:
    st.subheader("💰 Target Pendapatan")
    target_bersih = st.number_input("Harga Bersih (Pencairan) yang diinginkan:", min_value=1000, value=9850000, step=10000)

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
harga_optimum, rincian_potongan, total_potongan, hrg_stlh_voc, bd = find_optimum_price(
    target_bersih, voucher_cfg, st.session_state.biaya_df
)

# 2. MENAMPILKAN HARGA FINAL DI ATAS TABEL
st.markdown("---")
pct_total_potongan = (total_potongan / hrg_stlh_voc * 100) if hrg_stlh_voc > 0 else 0

c_res1, c_res2 = st.columns([1, 1])
c_res1.metric(label="🎯 Harga Jual Optimum (Harga Tampil)", value=format_rp(harga_optimum))
c_res2.metric(label="📉 Total Potongan Biaya & Asuransi", value=format_rp(total_potongan), delta=f"-{pct_total_potongan:.2f}%", delta_color="inverse")

# 3. TABEL DINAMIS (INPUT + OUTPUT GABUNGAN)
st.subheader("⚙️ 1. Rincian Biaya & Komponen")

display_df = st.session_state.biaya_df.copy()
display_df["Nominal Potongan"] = [f"- {format_rp(x)}" if aktif else "-" for x, aktif in zip(rincian_potongan, display_df["Aktif"])]

config_kolom = {
    "Aktif": st.column_config.CheckboxColumn("Status", default=True),
    "Deskripsi": st.column_config.TextColumn("Deskripsi Biaya / Komponen"),
    "Kategori": st.column_config.SelectboxColumn("Kategori (Wajib)", options=["Admin", "Layanan", "Asuransi"], required=True),
    "Tipe Cut": st.column_config.SelectboxColumn("Tipe Potongan", options=["Persentase (%)", "Persen dgn Batas Max", "Nominal (Rp)"], required=True),
    "Persentase (%)": st.column_config.NumberColumn("Persentase (%)", format="%.2f"),
    "Nominal / Batas Max (Rp)": st.column_config.NumberColumn("Nominal / Batas Max (Rp)", format="%d"),
    "Nominal Potongan": st.column_config.TextColumn("Nominal Potongan (Otomatis)", disabled=True)
}

edited_df = st.data_editor(
    display_df, 
    column_config=config_kolom, 
    num_rows="dynamic", 
    use_container_width=True,
    hide_index=True
)

new_state_df = edited_df.drop(columns=["Nominal Potongan"]).reset_index(drop=True)
if not new_state_df.equals(st.session_state.biaya_df.reset_index(drop=True)):
    st.session_state.biaya_df = new_state_df
    st.rerun()

# 4. TABEL LOGIC & SUMMARY CO-FUND VOUCHER
st.markdown("---")
st.subheader("📑 2. Summary & Logic Pencairan Shopee")

# Menghindari KeyError saat baris dihapus semua / error logic D <= 0
if hrg_stlh_voc > 0:
    logic_data = [
        {"Keterangan": "🔹 SUMMARY", "Nominal / Persentase": format_rp(bd['Harga Tampil']), "Catatan": ""},
        {"Keterangan": "Harga Setelah Potong Voucher", "Nominal / Persentase": format_rp(bd['D']), "Catatan": "Harga tampil (A) dikurangi total potongan voucher (B)."},
        {"Keterangan": "Biaya Admin di Seller Center", "Nominal / Persentase": format_rp(bd['Admin']), "Catatan": f"{format_pct(bd['N'])} dari Harga Setelah Potong Voucher"},
        {"Keterangan": "Biaya Layanan + Proses Pesanan", "Nominal / Persentase": format_rp(bd['Layanan']), "Catatan": f"{format_pct(bd['O'])} dari Harga Setelah Potong Voucher"},
        {"Keterangan": "Biaya Asuransi (Opsional)", "Nominal / Persentase": format_rp(bd['Asuransi']), "Catatan": "-"},
        
        {"Keterangan": "🔸 LOGIC", "Nominal / Persentase": "", "Catatan": ""},
        {"Keterangan": "Voucher Ditanggung Shopee", "Nominal / Persentase": format_rp(bd['M']), "Catatan": "Menghitung nilai subsidi yang harus dikembalikan Shopee."},
        {"Keterangan": "Tarif Admin Toko", "Nominal / Persentase": format_pct(bd['N']), "Catatan": "Mencari tahu persentase tarif komisi admin."},
        {"Keterangan": "Tarif Layanan Toko", "Nominal / Persentase": format_pct(bd['O']), "Catatan": "Mencari tahu persentase tarif layanan toko."},
        {"Keterangan": "Utang Selisih Admin", "Nominal / Persentase": format_rp(bd['P']), "Catatan": "Potongan admin dari subsidi Shopee."},
        {"Keterangan": "Utang Selisih Layanan", "Nominal / Persentase": format_rp(bd['Q']), "Catatan": "Potongan layanan dari subsidi Shopee."},
        {"Keterangan": "Total Utang Fee", "Nominal / Persentase": format_rp(bd['R']), "Catatan": "Total semua potongan biaya baru (utang selisih)."},
        
        {"Keterangan": "💵 HASIL PENCAIRAN", "Nominal / Persentase": "", "Catatan": ""},
        {"Keterangan": "Refund Bersih Shopee", "Nominal / Persentase": format_rp(bd['S']), "Catatan": "Uang subsidi bersih yang akan ditransfer Shopee ke Anda."},
        {"Keterangan": "Payout Awal Seller Center", "Nominal / Persentase": format_rp(bd['T']), "Catatan": "Uang yang sudah masuk ke saldo Anda di awal."},
        {"Keterangan": "Total Pendapatan Akhir", "Nominal / Persentase": format_rp(bd['U']), "Catatan": "Harga Bersih yang ditarik (Target Anda)."}
    ]
    
    st.dataframe(
        pd.DataFrame(logic_data),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Keterangan": st.column_config.TextColumn("Keterangan", width="medium"),
            "Nominal / Persentase": st.column_config.TextColumn("Nominal", width="small"),
            "Catatan": st.column_config.TextColumn("Catatan Deskripsi", width="large"),
        }
    )
    
    if bd['U'] == target_bersih:
        st.success(f"✅ **Verifikasi Akurat:** Total Pendapatan Akhir (**{format_rp(bd['U'])}**) sudah persis sama dengan Target Pendapatan Anda.")
else:
    st.warning("Menunggu data untuk dikalkulasi...")

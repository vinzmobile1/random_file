import streamlit as st

st.set_page_config(page_title="Kalkulator Harga Tampil Shopee", layout="wide")

def format_rp(angka):
    return f"Rp {int(round(angka)):,.0f}".replace(",", ".")

def format_pct(angka):
    return f"{angka * 100:.2f}%"

# --- FUNGSI PERHITUNGAN MAJU (Sesuai Logika Excel Anda) ---
def calculate_shopee(harga_tampil, config):
    A = harga_tampil
    
    # 1. VOUCHER
    if config['use_voucher']:
        B = min(A * config['v_pct'], config['v_max'])
        C = B * config['v_seller_pct']
    else:
        B = 0
        C = 0
        
    D = A - B
    
    # Mencegah error bagi nol jika D = 0
    if D <= 0:
        return 0, {}

    # 2. BIAYA LAYANAN
    E = round(D * config['admin_pct'])
    F = round(min(D * config['ongkir_pct'], config['ongkir_max']))
    G = round(min(D * config['mall_pct'], config['mall_max']))
    H = round(min(D * config['xtra_pct'], config['xtra_max']))
    I = config['proses_fee']
    J = round(D * config['asuransi_pct'])
    
    # SUMMARY
    K = E
    L = F + G + H + I
    
    # 3. LOGIC (Subsidi & Utang Fee)
    M = B - C
    N = K / D
    O = L / D
    
    P = round(N * M)
    Q = round(O * M)
    R = P + Q
    
    S = M - R
    T = D - J - K - L
    
    U = S + T # Total Pendapatan Akhir (Harga Bersih)
    
    # Dictionary untuk menyimpan seluruh data breakdown
    breakdown = {
        'A': A, 'B': B, 'C': C, 'D': D, 'E': E, 'F': F, 'G': G, 'H': H, 'I': I, 'J': J,
        'K': K, 'L': L, 'M': M, 'N': N, 'O': O, 'P': P, 'Q': Q, 'R': R, 'S': S, 'T': T, 'U': U
    }
    
    return U, breakdown

# --- FUNGSI PENCARIAN REVERSE (Mencari Harga Tampil) ---
def find_harga_tampil(target_bersih, config):
    low = target_bersih
    high = target_bersih * 3.0 # Batas atas tebakan (3x lipat)
    
    # Binary Search untuk akurasi mendekati Rp 1
    for _ in range(100): 
        mid = (low + high) / 2
        current_bersih, _ = calculate_shopee(mid, config)
        
        if current_bersih < target_bersih:
            low = mid
        else:
            high = mid
            
    # Kembalikan nilai tengah dengan pembulatan ke atas/bawah yang paling pas
    _, breakdown = calculate_shopee(round(high), config)
    return round(high), breakdown


# --- USER INTERFACE STREAMLIT ---
st.title("🍊 Kalkulator Harga Tampil Shopee")
st.markdown("Aplikasi ini menghitung **Harga Tampil (Markup)** otomatis berdasarkan **Harga Bersih** yang Anda inginkan, dengan mempertimbangkan skema voucher dan potongan layanan/admin Shopee.")

# SIDEBAR: Konfigurasi Biaya (Bisa diedit manual oleh user)
with st.sidebar:
    st.header("⚙️ Pengaturan Biaya Shopee")
    st.caption("Ubah persentase/maksimal biaya sesuai kebijakan terbaru Shopee.")
    
    admin_pct = st.number_input("Biaya Admin (%)", value=4.70, step=0.1) / 100
    
    ongkir_pct = st.number_input("Gratis Ongkir XTRA (%)", value=1.00, step=0.1) / 100
    ongkir_max = st.number_input("Max Ongkir XTRA (Rp)", value=40000, step=1000)
    
    mall_pct = st.number_input("Layanan Mall (%)", value=1.80, step=0.1) / 100
    mall_max = st.number_input("Max Layanan Mall (Rp)", value=50000, step=1000)
    
    xtra_pct = st.number_input("Promo XTRA+ (%)", value=6.50, step=0.1) / 100
    xtra_max = st.number_input("Max Promo XTRA (Rp)", value=80000, step=1000)
    
    asuransi_pct = st.number_input("Biaya Asuransi (%)", value=0.50, step=0.1) / 100
    proses_fee = st.number_input("Biaya Proses (Rp)", value=1250, step=250)

# KONTEN UTAMA
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("💰 Input Target Pendapatan")
    target_bersih = st.number_input("Masukkan Harga Bersih yang diinginkan (Pencairan):", min_value=1000, value=9850000, step=10000)
    
    use_voucher = st.radio("Apakah menggunakan Voucher Diskon?", ("Tanpa Voucher", "Gunakan Voucher")) == "Gunakan Voucher"

with col2:
    if use_voucher:
        st.subheader("🎟️ Input Data Voucher")
        v_pct = st.number_input("% Voucher", value=30.0, step=1.0) / 100
        v_max = st.number_input("Max Voucher (Rp)", value=500000, step=10000)
        
        c1, c2 = st.columns(2)
        with c1:
            v_shopee_pct = st.number_input("% Ditanggung Shopee", value=65.0, step=1.0) / 100
        with c2:
            v_seller_pct = st.number_input("% Ditanggung Seller", value=35.0, step=1.0) / 100
            
        if abs((v_shopee_pct + v_seller_pct) - 1.0) > 0.01:
            st.error("Total % Ditanggung Shopee & Seller harus 100%!")

# Siapkan Config Dictionary
config = {
    'use_voucher': use_voucher,
    'v_pct': v_pct if use_voucher else 0,
    'v_max': v_max if use_voucher else 0,
    'v_shopee_pct': v_shopee_pct if use_voucher else 0,
    'v_seller_pct': v_seller_pct if use_voucher else 0,
    'admin_pct': admin_pct,
    'ongkir_pct': ongkir_pct, 'ongkir_max': ongkir_max,
    'mall_pct': mall_pct, 'mall_max': mall_max,
    'xtra_pct': xtra_pct, 'xtra_max': xtra_max,
    'asuransi_pct': asuransi_pct,
    'proses_fee': proses_fee
}

if st.button("🔄 Hitung Harga Tampil", type="primary", use_container_width=True):
    harga_tampil, bd = find_harga_tampil(target_bersih, config)
    
    st.success(f"### 🎉 Harga Tampil yang harus diset di Shopee: {format_rp(harga_tampil)}")
    
    st.markdown("---")
    st.subheader("📑 Bukti Perhitungan (Breakdown)")
    st.markdown("*Angka di bawah ini mereplika perhitungan di Excel yang Anda berikan.*")
    
    # Tabel Data
    tab1, tab2, tab3 = st.tabs(["Informasi Voucher & Harga", "Rincian Biaya Layanan", "Logika Pencairan (Summary)"])
    
    with tab1:
        st.write(f"**A. Subtotal Pesanan/Harga Tampil:** {format_rp(bd['A'])}")
        st.write(f"**B. Voucher Terpotong di Seller Center:** {format_rp(bd['B'])}")
        st.write(f"**C. Voucher Ditanggung Seller:** {format_rp(bd['C'])}")
        st.write(f"**D. Harga Setelah Potong Voucher (A-B):** {format_rp(bd['D'])}")
        
    with tab2:
        st.write(f"**E. Biaya Admin ({format_pct(admin_pct)}):** {format_rp(bd['E'])}")
        st.write(f"**F. Gratis Ongkir XTRA ({format_pct(ongkir_pct)} - Max {format_rp(ongkir_max)}):** {format_rp(bd['F'])}")
        st.write(f"**G. Layanan Mall ({format_pct(mall_pct)} - Max {format_rp(mall_max)}):** {format_rp(bd['G'])}")
        st.write(f"**H. Promo XTRA+ ({format_pct(xtra_pct)} - Max {format_rp(xtra_max)}):** {format_rp(bd['H'])}")
        st.write(f"**I. Proses Pesanan:** {format_rp(bd['I'])}")
        st.write(f"**J. Biaya Asuransi ({format_pct(asuransi_pct)}):** {format_rp(bd['J'])}")
        st.write(f"**Total Biaya Layanan:** {format_rp(bd['J'] + bd['K'] + bd['L'])}")
        
    with tab3:
        st.write(f"**K. Total Admin di Seller Center (E):** {format_rp(bd['K'])}")
        st.write(f"**L. Biaya Layanan + Proses Pesanan (F+G+H+I):** {format_rp(bd['L'])}")
        st.write(f"**M. Voucher Ditanggung Shopee (B-C):** {format_rp(bd['M'])}")
        st.write(f"**N. Tarif Admin Toko K/D:** {format_pct(bd['N'])}")
        st.write(f"**O. Tarif Layanan Toko L/D:** {format_pct(bd['O'])}")
        st.write(f"**P. Utang Selisih Admin (N*M):** {format_rp(bd['P'])}")
        st.write(f"**Q. Utang Selisih Layanan (O*M):** {format_rp(bd['Q'])}")
        st.write(f"**R. Total Utang Fee (P+Q):** {format_rp(bd['R'])}")
        st.write(f"**S. Refund Bersih Shopee (M-R):** {format_rp(bd['S'])}")
        st.write(f"**T. Payout Awal Seller Center (D-J-K-L):** {format_rp(bd['T'])}")
        st.divider()
        st.markdown(f"#### **U. Total Pendapatan Akhir / Harga Bersih (S+T) : {format_rp(bd['U'])}**")
        if bd['U'] == target_bersih:
            st.success("✅ Terverifikasi: Harga Bersih perhitungan SAMA PERSIS dengan Target Input!")
        else:
            st.warning("⚠️ Ada selisih pembulatan sebesar beberapa Rupiah. Hal ini wajar karena sistem Shopee membulatkan per Rupiah tiap transaksi.")

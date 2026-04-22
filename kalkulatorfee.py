import streamlit as st
import math

st.set_page_config(layout="wide")

# ---------- STYLE ----------
st.markdown("""
<style>
.card {padding:16px;border-radius:12px;border:1px solid #333;margin-bottom:12px;background:#111;}
.blue {color:#4cc9f0;}
.orange {color:#f77f00;}
.green {color:#2a9d8f;}
.big {font-size:24px;font-weight:bold;}
.box {padding:14px;border-radius:10px;background:#1a1a1a;margin-top:8px;}
.warn {background:#2b1d12;border:1px solid #f77f00;}
.ok {background:#0f2a1d;border:1px solid #2a9d8f;}
</style>
""", unsafe_allow_html=True)

def rp(x): return f"Rp {x:,.0f}".replace(",", ".")

# ---------- INPUT ----------
st.title("Logika Perhitungan Dinamis")

net = st.number_input("Target Net", value=7150000)

fees = [
    {"name":"Fee Kategori","pct":4.7,"type":"PCT","max":0,"nominal":0},
    {"name":"Asuransi","pct":0.5,"type":"PCT","max":0,"nominal":0},
    {"name":"Payment Fee","pct":1.8,"type":"CAPPED_PCT","max":50000,"nominal":0},
    {"name":"Promo","pct":4.5,"type":"CAPPED_PCT","max":60000,"nominal":0},
    {"name":"GoX","pct":0.5,"type":"CAPPED_PCT","max":40000,"nominal":0},
    {"name":"Proses","pct":0,"type":"NOMINAL","max":0,"nominal":1250},
]

if st.button("🔥 Hitung"):

    # ---------- STEP 1 ----------
    st.markdown("### 1️⃣ Total Biaya Persentase (Awal)")
    total_pct = sum(f["pct"] for f in fees if f["type"]!="NOMINAL")
    pembagi_awal = 1 - total_pct/100

    st.markdown('<div class="card">', unsafe_allow_html=True)
    for f in fees:
        if f["type"]!="NOMINAL":
            st.write(f'{f["name"]}: {f["pct"]:.2f}%')
    st.write("---")
    st.write(f"Rumus: 100% - {total_pct:.2f}%")
    st.markdown(f'<span class="blue">Angka Pembagi Awal: {pembagi_awal:.4f}</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ---------- STEP 2 ----------
    st.markdown("### 2️⃣ Total Biaya Nominal & Target Net")
    nominal_sum = sum(f["nominal"] for f in fees)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write(f"Target Net: {rp(net)}")
    st.write(f"Nominal: + {rp(nominal_sum)}")
    penambah_awal = net + nominal_sum
    st.markdown(f'<span class="blue">Angka Penambah Awal: {rp(penambah_awal)}</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ---------- STEP 3 ----------
    harga_tebakan = penambah_awal / pembagi_awal
    st.markdown("### 3️⃣ Harga Simulasi (Tebakan)")
    st.markdown(f'<div class="box">{rp(penambah_awal)} / {pembagi_awal:.4f} = <span class="blue">{rp(harga_tebakan)}</span></div>', unsafe_allow_html=True)

    # ---------- STEP 4 ----------
    st.markdown("### 4️⃣ Deteksi Batas Maksimal")

    capped_results = []
    for f in fees:
        if f["type"]=="CAPPED_PCT":
            calc = harga_tebakan * f["pct"]/100
            kena = calc > f["max"]

            cls = "warn" if kena else "box"
            st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
            st.write(f"{f['name']}")
            st.write(f"Fee Normal: {f['pct']}% x {rp(harga_tebakan)} = {rp(calc)}")
            st.write(f"Limit: {rp(f['max'])}")

            if kena:
                st.markdown(f'<span class="orange">Kena limit → jadi {rp(f["max"])}</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span class="blue">Normal</span>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

            capped_results.append((f, kena))

    # ---------- STEP 5 ----------
    st.markdown("### 5️⃣ Susunan Final")

    pembagi = 1
    penambah = net + nominal_sum

    for f in fees:
        if f["type"]=="PCT":
            pembagi -= f["pct"]/100

    for f, kena in capped_results:
        if kena:
            penambah += f["max"]
        else:
            pembagi -= f["pct"]/100

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write(f"Pembagi Akhir: {pembagi:.4f}")
    st.write(f"Penambah Akhir: {rp(penambah)}")

    harga_raw = penambah / pembagi
    st.markdown(f'<div class="box">{rp(penambah)} / {pembagi:.4f} = {rp(harga_raw)}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ---------- STEP 6 ----------
    harga_final = math.ceil(harga_raw/1000)*1000

    st.markdown("### 6️⃣ Pembulatan")
    st.markdown(f'<div class="card big">Harga Tampil: <span class="green">{rp(harga_final)}</span></div>', unsafe_allow_html=True)

    # ---------- VALIDATION ----------
    st.markdown("### ✅ Crosscheck")

    total = 0
    for f in fees:
        if f["type"]=="PCT":
            val = harga_final * f["pct"]/100
        elif f["type"]=="NOMINAL":
            val = f["nominal"]
        else:
            val = min(harga_final*f["pct"]/100, f["max"])
        total += val
        st.write(f"{f['name']}: {rp(val)}")

    st.write("---")
    st.success(f"Net diterima: {rp(harga_final - total)}")

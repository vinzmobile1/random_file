import streamlit as st
import math
import uuid

# ---------- Config ----------
st.set_page_config(layout="wide")

# ---------- Style ----------
st.markdown("""
<style>
.card {
    padding: 16px;
    border-radius: 12px;
    background: #111;
    border: 1px solid #333;
    margin-bottom: 10px;
}
.result-box {
    padding: 20px;
    border-radius: 12px;
    background: #0d1b2a;
    border: 1px solid #1b263b;
}
.big-text {
    font-size: 28px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ---------- Helpers ----------
def generate_id():
    return str(uuid.uuid4())[:8]

def format_idr(num):
    return f"Rp {num:,.0f}".replace(",", ".")

# ---------- Core Logic ----------
def calculate(net, fees):
    debug = []

    strict_pct_total = 0
    capped_pct_sum = 0
    nominal_sum = 0

    for f in fees:
        pct = f["pct"] / 100

        if f["type"] == "PCT":
            strict_pct_total += pct
        elif f["type"] == "CAPPED_PCT":
            capped_pct_sum += pct
        elif f["type"] == "NOMINAL":
            nominal_sum += f["nominal"]

    all_pct = strict_pct_total + capped_pct_sum

    harga_tebakan = (net + nominal_sum) / max(0.0001, (1 - all_pct))
    debug.append(f"Harga Tebakan: {harga_tebakan:,.0f}")

    pembagi = 1 - strict_pct_total
    penambah = net + nominal_sum

    breakdown = []

    for f in fees:
        pct = f["pct"] / 100

        if f["type"] == "CAPPED_PCT":
            calc = harga_tebakan * pct

            if calc > f["max"]:
                penambah += f["max"]
                breakdown.append((f["name"], f["max"], "CAPPED ✅"))
            else:
                pembagi -= pct
                breakdown.append((f["name"], calc, "NORMAL"))
        elif f["type"] == "PCT":
            breakdown.append((f["name"], pct, "PCT"))
        else:
            breakdown.append((f["name"], f["nominal"], "NOMINAL"))

    harga = penambah / max(0.0001, pembagi)
    harga = math.ceil(harga / 1000) * 1000

    # validasi
    total_potongan = 0
    detail_final = []

    for f in fees:
        pct = f["pct"] / 100

        if f["type"] == "PCT":
            val = harga * pct
        elif f["type"] == "NOMINAL":
            val = f["nominal"]
        else:
            calc = harga * pct
            val = min(calc, f["max"])

        total_potongan += val
        detail_final.append((f["name"], val))

    bersih = harga - total_potongan

    return harga, bersih, total_potongan, breakdown, detail_final, debug

# ---------- State ----------
if "fees" not in st.session_state:
    st.session_state.fees = [
        {"id": generate_id(), "name": "Fee Kategori", "type": "PCT", "pct": 4.7, "max": 0, "nominal": 0},
        {"id": generate_id(), "name": "Asuransi", "type": "PCT", "pct": 0.5, "max": 0, "nominal": 0},
    ]

# ---------- UI ----------
st.title("💰 Kalkulator Harga (Advanced)")

colA, colB = st.columns([2, 1])

with colA:
    st.subheader("Input")
    net = st.number_input("Net Target", value=7150000)

    st.subheader("Fees")

    for i, f in enumerate(st.session_state.fees):
        st.markdown('<div class="card">', unsafe_allow_html=True)

        c1, c2, c3, c4, c5 = st.columns(5)

        f["name"] = c1.text_input("Nama", f["name"], key=f"name_{i}")
        f["type"] = c2.selectbox("Type", ["PCT", "CAPPED_PCT", "NOMINAL"], key=f"type_{i}")
        f["pct"] = c3.number_input("%", value=f["pct"], key=f"pct_{i}")
        f["max"] = c4.number_input("Max", value=f["max"], key=f"max_{i}")
        f["nominal"] = c5.number_input("Nominal", value=f["nominal"], key=f"nom_{i}")

        if st.button("❌ Hapus", key=f"del_{i}"):
            st.session_state.fees.pop(i)
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("➕ Tambah Fee"):
        st.session_state.fees.append(
            {"id": generate_id(), "name": "Fee Baru", "type": "PCT", "pct": 0, "max": 0, "nominal": 0}
        )
        st.rerun()

with colB:
    st.subheader("Hasil")

    if st.button("🔥 Hitung"):
        harga, bersih, potongan, breakdown, detail_final, debug = calculate(net, st.session_state.fees)

        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        st.markdown(f'<div class="big-text">{format_idr(harga)}</div>', unsafe_allow_html=True)
        st.caption("Harga Tampil")
        st.markdown('</div>', unsafe_allow_html=True)

        st.success(f"Bersih: {format_idr(bersih)}")
        st.warning(f"Total Potongan: {format_idr(potongan)}")

        st.divider()

        st.subheader("Breakdown Final")
        for name, val in detail_final:
            st.write(f"{name}: {format_idr(val)}")

        st.divider()

        st.subheader("Debug / Transparansi")
        for d in debug:
            st.code(d)

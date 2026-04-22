import streamlit as st
import math
import uuid

st.set_page_config(layout="wide")

def rp(x): return f"Rp {x:,.0f}".replace(",", ".")

def gid(): return str(uuid.uuid4())[:6]

# ---------- STATE ----------
if "fees" not in st.session_state:
    st.session_state.fees = []

# ---------- INPUT ----------
st.title("🔬 Kalkulator Transparan (Manual Fees)")

net = st.number_input("Target Net", value=7150000)

st.subheader("📦 Input Fees Manual")

for i, f in enumerate(st.session_state.fees):
    col1, col2, col3, col4, col5 = st.columns(5)

    f["name"] = col1.text_input("Nama", f["name"], key=f"name_{i}")

    f["type"] = col2.selectbox(
        "Type",
        ["PCT", "CAPPED_PCT", "NOMINAL"],
        key=f"type_{i}"
    )

    if f["type"] == "PCT":
        f["pct"] = col3.number_input("%", value=f.get("pct", 0.0), key=f"pct_{i}")
        f["max"] = 0
        f["nominal"] = 0

    elif f["type"] == "CAPPED_PCT":
        f["pct"] = col3.number_input("%", value=f.get("pct", 0.0), key=f"pct_{i}")
        f["max"] = col4.number_input("Max", value=f.get("max", 0.0), key=f"max_{i}")
        f["nominal"] = 0

    else:
        f["nominal"] = col5.number_input("Nominal", value=f.get("nominal", 0.0), key=f"nom_{i}")
        f["pct"] = 0
        f["max"] = 0

    if col5.button("❌", key=f"del_{i}"):
        st.session_state.fees.pop(i)
        st.rerun()

st.button("➕ Tambah Fee", on_click=lambda: st.session_state.fees.append({
    "id": gid(), "name": "Fee Baru", "type": "PCT", "pct": 0.0, "max": 0.0, "nominal": 0.0
}))

# ---------- CALC ----------
if st.button("🔥 Hitung"):

    fees = st.session_state.fees

    # STEP 1
    strict = sum(f["pct"] for f in fees if f["type"]=="PCT")
    capped = sum(f["pct"] for f in fees if f["type"]=="CAPPED_PCT")
    total_pct = strict + capped
    pembagi_awal = 1 - total_pct/100

    st.header("1️⃣ Pembagi Awal")
    st.write(f"Total %: {total_pct:.2f}%")
    st.code(f"1 - {total_pct:.2f}% = {pembagi_awal:.4f}")

    # STEP 2
    nominal_sum = sum(f["nominal"] for f in fees)
    penambah_awal = net + nominal_sum

    st.header("2️⃣ Penambah Awal")
    st.write(rp(penambah_awal))

    # STEP 3
    harga_tebakan = penambah_awal / max(0.0001, pembagi_awal)

    st.header("3️⃣ Harga Tebakan")
    st.write(rp(harga_tebakan))

    # STEP 4 (DETAIL)
    st.header("4️⃣ Evaluasi Limit")

    evaluasi = []

    for f in fees:
        if f["type"]=="CAPPED_PCT":
            val = harga_tebakan * f["pct"]/100
            kena = val > f["max"]
            final = f["max"] if kena else val

            st.write("---")
            st.write(f"{f['name']}")
            st.write(f"{f['pct']}% x {rp(harga_tebakan)} = {rp(val)}")
            st.write(f"Limit: {rp(f['max'])}")

            if kena:
                st.error(f"KENA LIMIT → {rp(final)}")
            else:
                st.success(f"NORMAL → {rp(final)}")

            evaluasi.append((f, kena, final))

    # STEP 5
    st.header("5️⃣ Final Formula")

    pembagi = 1
    penambah = net + nominal_sum

    for f in fees:
        if f["type"]=="PCT":
            pembagi -= f["pct"]/100

    for f, kena, final in evaluasi:
        if kena:
            penambah += final
        else:
            pembagi -= f["pct"]/100

    harga_raw = penambah / max(0.0001, pembagi)

    st.write(f"Pembagi: {pembagi:.4f}")
    st.write(f"Penambah: {rp(penambah)}")
    st.write(f"Harga Raw: {rp(harga_raw)}")

    # STEP 6
    harga_final = math.ceil(harga_raw/1000)*1000

    st.header("6️⃣ Harga Final")
    st.success(rp(harga_final))

    # VALIDASI
    st.header("✅ Crosscheck")

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

    net_real = harga_final - total
    st.write("---")
    st.success(f"Net diterima: {rp(net_real)}")

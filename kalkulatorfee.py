import streamlit as st
import math

st.set_page_config(layout="wide")

def rp(x): return f"Rp {x:,.0f}".replace(",", ".")

st.title("🔬 Kalkulator Transparan (Full Audit Mode)")

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

    # ================= STEP 1 =================
    st.header("1️⃣ Total % (Awal)")

    strict = sum(f["pct"] for f in fees if f["type"]=="PCT")
    capped = sum(f["pct"] for f in fees if f["type"]=="CAPPED_PCT")
    total_pct = strict + capped

    pembagi_awal = 1 - total_pct/100

    st.write(f"Strict %: {strict:.2f}%")
    st.write(f"Capped %: {capped:.2f}%")
    st.write(f"Total %: {total_pct:.2f}%")
    st.code(f"Pembagi Awal = 1 - {total_pct:.2f}% = {pembagi_awal:.4f}")

    # ================= STEP 2 =================
    st.header("2️⃣ Penambah Awal")

    nominal_sum = sum(f["nominal"] for f in fees)
    penambah_awal = net + nominal_sum

    st.write(f"Net: {rp(net)}")
    st.write(f"Nominal Sum: {rp(nominal_sum)}")
    st.code(f"Penambah Awal = {rp(net)} + {rp(nominal_sum)} = {rp(penambah_awal)}")

    # ================= STEP 3 =================
    st.header("3️⃣ Harga Tebakan")

    harga_tebakan = penambah_awal / pembagi_awal
    st.code(f"{rp(penambah_awal)} / {pembagi_awal:.4f} = {rp(harga_tebakan)}")

    # ================= STEP 4 =================
    st.header("4️⃣ Evaluasi Limit (DETAIL BANGET)")

    evaluasi = []

    for f in fees:
        if f["type"] == "CAPPED_PCT":
            pct_val = harga_tebakan * f["pct"]/100
            kena = pct_val > f["max"]

            final_val = f["max"] if kena else pct_val
            delta = pct_val - final_val

            st.markdown("---")
            st.subheader(f["name"])

            st.write(f"Rumus: {f['pct']}% x {rp(harga_tebakan)}")
            st.write(f"Hasil: {rp(pct_val)}")
            st.write(f"Limit: {rp(f['max'])}")

            if kena:
                st.error(f"KENA LIMIT → {rp(final_val)} (dipotong {rp(delta)})")
            else:
                st.success(f"NORMAL → {rp(final_val)}")

            evaluasi.append({
                "fee": f,
                "kena": kena,
                "nilai_awal": pct_val,
                "nilai_final": final_val
            })

    # ================= STEP 5 =================
    st.header("5️⃣ Rebuild Formula Final (SUPER TRANSPARAN)")

    pembagi = 1
    penambah = net + nominal_sum

    st.subheader("Pembagi:")
    st.write("Start: 1.0000")

    for f in fees:
        if f["type"]=="PCT":
            val = f["pct"]/100
            pembagi -= val
            st.write(f"- {f['name']} ({val:.4f}) → {pembagi:.4f}")

    for e in evaluasi:
        if not e["kena"]:
            val = e["fee"]["pct"]/100
            pembagi -= val
            st.write(f"- {e['fee']['name']} ({val:.4f}) → {pembagi:.4f}")

    st.subheader("Penambah:")
    st.write(rp(penambah))

    for e in evaluasi:
        if e["kena"]:
            penambah += e["nilai_final"]
            st.write(f"+ {e['fee']['name']} limit {rp(e['nilai_final'])} → {rp(penambah)}")

    st.code(f"Harga Mentah = {rp(penambah)} / {pembagi:.4f}")

    harga_raw = penambah / pembagi

    # ================= STEP 6 =================
    st.header("6️⃣ Rounding")

    harga_final = math.ceil(harga_raw/1000)*1000
    delta_round = harga_final - harga_raw

    st.write(f"Sebelum: {rp(harga_raw)}")
    st.write(f"Sesudah: {rp(harga_final)}")
    st.write(f"Delta rounding: {rp(delta_round)}")

    # ================= VALIDATION =================
    st.header("✅ VALIDASI FINAL")

    total = 0
    for f in fees:
        if f["type"]=="PCT":
            val = harga_final * f["pct"]/100
        elif f["type"]=="NOMINAL":
            val = f["nominal"]
        else:
            val = min(harga_final*f["pct"]/100, f["max"])

        total += val
        st.write(f"{f['name']} → {rp(val)}")

    net_real = harga_final - total
    selisih = net_real - net

    st.write("---")
    st.success(f"Net Real: {rp(net_real)}")
    st.warning(f"Selisih dari target: {rp(selisih)}")

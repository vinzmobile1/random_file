import streamlit as st
import math
import uuid

# ---------- Helpers ----------
def generate_id():
    return str(uuid.uuid4())[:8]


def format_idr(num: float) -> str:
    return f"Rp {num:,.0f}".replace(",", ".")


# ---------- Core Logic ----------
def calculate(net, fees):
    n_net = float(net or 0)

    strict_pct_total = 0
    capped_pct_sum = 0
    nominal_sum = 0

    initial_pcts = []
    initial_nominals = []

    for f in fees:
        pct = float(f["pct"] or 0) / 100
        nominal = float(f["nominal"] or 0)

        if f["type"] == "PCT":
            strict_pct_total += pct
            initial_pcts.append((f["name"], pct))

        elif f["type"] == "CAPPED_PCT":
            capped_pct_sum += pct
            initial_pcts.append((f["name"], pct))

        elif f["type"] == "NOMINAL":
            nominal_sum += nominal
            initial_nominals.append((f["name"], nominal))

    all_pcts_total = strict_pct_total + capped_pct_sum

    pembagi_awal = 1 - all_pcts_total
    aman_pembagi_awal = pembagi_awal if pembagi_awal > 0 else 0.0001

    harga_tebakan = (n_net + nominal_sum) / aman_pembagi_awal

    pembagi_akhir = 1 - strict_pct_total
    penambah_akhir = n_net + nominal_sum

    final_pcts = list(initial_pcts)
    final_nominals = list(initial_nominals)

    for f in fees:
        if f["type"] == "CAPPED_PCT":
            pct = float(f["pct"] or 0) / 100
            max_val = float(f["max"] or 0)

            cost_tebakan = harga_tebakan * pct
            is_max = cost_tebakan > max_val

            if is_max:
                penambah_akhir += max_val
                final_nominals.append((f["name"] + " (Limit)", max_val))
            else:
                pembagi_akhir -= pct
                final_pcts.append((f["name"], pct))

    aman_pembagi_akhir = pembagi_akhir if pembagi_akhir > 0 else 0.0001
    harga_tampil_raw = penambah_akhir / aman_pembagi_akhir

    harga_tampil = math.ceil(harga_tampil_raw / 1000) * 1000

    # pembuktian
    total_potongan = 0

    for f in fees:
        pct = float(f["pct"] or 0) / 100
        nominal = float(f["nominal"] or 0)
        max_val = float(f["max"] or 0)

        if f["type"] == "PCT":
            potongan = harga_tampil * pct
        elif f["type"] == "NOMINAL":
            potongan = nominal
        else:
            calc = harga_tampil * pct
            potongan = max_val if calc > max_val else calc

        total_potongan += potongan

    hasil_bersih = harga_tampil - total_potongan

    return {
        "harga_tampil": harga_tampil,
        "hasil_bersih": hasil_bersih,
        "total_potongan": total_potongan,
    }


# ---------- UI ----------
st.set_page_config(page_title="Kalkulator Harga", layout="wide")

st.title("Kalkulator Harga Tampil (Streamlit)")

# state
if "fees" not in st.session_state:
    st.session_state.fees = [
        {"id": generate_id(), "name": "Fee Kategori", "type": "PCT", "pct": 4.7, "max": 0, "nominal": 0},
        {"id": generate_id(), "name": "Asuransi", "type": "PCT", "pct": 0.5, "max": 0, "nominal": 0},
    ]

net = st.number_input("Net yang diinginkan", value=7150000)

st.subheader("Fees")

for i, f in enumerate(st.session_state.fees):
    col1, col2, col3, col4, col5 = st.columns(5)

    f["name"] = col1.text_input("Nama", f["name"], key=f"name_{i}")
    f["type"] = col2.selectbox("Type", ["PCT", "CAPPED_PCT", "NOMINAL"], index=["PCT","CAPPED_PCT","NOMINAL"].index(f["type"]), key=f"type_{i}")
    f["pct"] = col3.number_input("Pct %", value=float(f["pct"]), key=f"pct_{i}")
    f["max"] = col4.number_input("Max", value=float(f["max"]), key=f"max_{i}")
    f["nominal"] = col5.number_input("Nominal", value=float(f["nominal"]), key=f"nom_{i}")

    if st.button("Hapus", key=f"del_{i}"):
        st.session_state.fees.pop(i)
        st.rerun()

if st.button("Tambah Fee"):
    st.session_state.fees.append(
        {"id": generate_id(), "name": "Fee Baru", "type": "PCT", "pct": 0, "max": 0, "nominal": 0}
    )
    st.rerun()

# calculate
if st.button("Hitung"):
    result = calculate(net, st.session_state.fees)

    st.success(f"Harga Tampil: {format_idr(result['harga_tampil'])}")
    st.info(f"Hasil Bersih: {format_idr(result['hasil_bersih'])}")
    st.warning(f"Total Potongan: {format_idr(result['total_potongan'])}")

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Set konfigurasi halaman web
st.set_page_config(page_title="Simulator Hidrologi Padi Nanjungan", layout="wide")

st.title("🌾 Simulator Hidrologi & Neraca Air Padi Sawah")
st.markdown("### Studi Kasus: Desa Nanjungan (Model Interaktif Berbasis Basis Data & AI)")
st.write("Aplikasi ini mensimulasikan kebutuhan air tanaman (ETc) vs pasokan air (Hujan) serta menganalisis risiko defisit air menggunakan pembatas Kelembaban Tanah AI (Threshold 0.80) sesuai standar FAO-56.")

# 1. Load data CSV yang sudah di-update
@st.cache_data
def load_data():
    df = pd.read_csv("dasarian_et0_hujan_data_nanjungan.csv")
    return df

df = load_data()

# 2. Sidebar Input Slider untuk Awal Tanam
st.sidebar.header("Konfigurasi Masa Tanam")
awal_tanam = st.sidebar.slider("Pilih Dasarian Awal Tanam:", min_value=1, max_value=36, value=2)

# Nilai Kc Padi (11 Dasarian siklus hidup)
kc_padi = [1.20, 1.20, 1.20, 1.32, 1.40, 1.40, 1.35, 1.24, 1.24, 1.12, 1.12]

# Hitung urutan dasarian berdasarkan simulasi slider awal tanam
urutan_dasarian = []
for i in range(11):
    idx = (awal_tanam - 1 + i) % 36
    urutan_dasarian.append(idx + 1)

# Ambil data dinamis dari dataframe berdasarkan urutan dasarian dari slider
hujan_simulasi = []
et0_simulasi = []
kelembaban_simulasi = []

for d in urutan_dasarian:
    row = df[df['Dasarian'] == d].iloc[0]
    hujan_simulasi.append(row['PRECTOTCORR'])
    et0_simulasi.append(row['ET0'])
    kelembaban_simulasi.append(row['GWETROOT']) # Membaca kolom kelembaban tanah baru

# Hitung Kebutuhan Air (ETc)
etc_simulasi = [et0 * kc for et0, kc in zip(et0_simulasi, kc_padi)]

# =========================================================
# LOGIKA EVALUASI NERACA AIR DENGAN PEMBATAS KELEMBABAN 0.80
# =========================================================
total_defisit_36_opsi = []

for opsi_start in range(1, 37):
    defisit_opsi_ini = 0
    for i in range(11):
        idx_d = (opsi_start - 1 + i) % 36
        row_d = df[df['Dasarian'] == (idx_d + 1)].iloc[0]
        
        hujan_d = row_d['PRECTOTCORR']
        etc_d = row_d['ET0'] * kc_padi[i]
        gw_d = row_d['GWETROOT'] # Nilai kelembaban tanah opsi ini
        
        # Evaluasi risiko difokuskan pada fase kritis pertengahan (fase generatif)
        if 4 <= i <= 8:
            if hujan_d < etc_d:
                # Logika pembatas: hanya dihitung defisit jika kelembaban tanah di bawah 0.80
                if gw_d < 0.80:
                    defisit_opsi_ini += (etc_d - hujan_d)
                    
    total_defisit_36_opsi.append(defisit_opsi_ini)

# =========================================================

# 3. TAMPILKAN GRAFIK UTAMA (DENGAN DOUBLE Y-AXIS)
st.subheader("📊 Grafik Analisis Hidrologi & Kelembaban Tanah Dinamis")
st.write("Geser slider di sidebar untuk melihat respons kelembaban tanah dan neraca air sepanjang 11 dasarian hidup tanaman.")

fig1, ax1 = plt.subplots(figsize=(12, 5))
label_dasarian = [f"D-{d}\n(Fase {i+1})" for i, d in enumerate(urutan_dasarian)]
x = np.arange(len(label_dasarian))

# Sumbu Y Kiri untuk volume air (mm)
ax1.bar(x - 0.2, hujan_simulasi, width=0.4, label="Curah Hujan (mm)", color="skyblue", alpha=0.8)
ax1.plot(x, etc_simulasi, label="Kebutuhan Air / ETc (mm)", color="red", marker="o", linewidth=2)
ax1.plot(x, et0_simulasi, label="Evapotranspirasi / ET0 (mm)", color="orange", linestyle="--", marker="x")
ax1.set_ylabel("Volume Air (mm/Dasarian)", color="darkblue")
ax1.set_xlabel("Siklus Pertumbuhan Padi (Urutan Dasarian Aktual Berdasarkan Slider)")
ax1.set_xticks(x)
ax1.set_xticklabels(label_dasarian)
ax1.grid(True, alpha=0.3)

# Sumbu Y Kanan khusus untuk Kelembaban Tanah (GWETROOT)
ax2 = ax1.twinx()
ax2.plot(x, kelembaban_simulasi, label="Kelembaban Tanah (GWETROOT)", color="green", linestyle="-.", marker="s", linewidth=2)
ax2.set_ylabel("Kadar Kelembaban Tanah (Zona Akar)", color="green")
ax2.set_ylim(0, 1.2)
ax2.axhline(0.80, color='red', linestyle=':', alpha=0.7, label='Batas Kritis FAO-56 (0.80)')

# Menggabungkan legenda kedua sumbu Y
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")
ax1.axvspan(3.5, 7.5, color='yellow', alpha=0.15, label='Fase Kritis')
st.pyplot(fig1)


# 4. GRAFIK REKOMENDASI 36 OPSI KALENDER TANAM
st.subheader("📉 Analisis Risiko Defisit Air pada 36 Opsi Kalender Tanam Padi (IP 300)")
st.write("Grafik di bawah ini secara otomatis mengunci rekomendasi tanggal tanam dengan mempertimbangkan filter kelembaban tanah 0.80.")

fig2, ax3 = plt.subplots(figsize=(14, 4))
opsi_x = np.arange(1, 37)
colors = plt.cm.Blues_r(np.array(total_defisit_36_opsi) / max(total_defisit_36_opsi) if max(total_defisit_36_opsi) > 0 else 1)
bars = ax3.bar(opsi_x, total_defisit_36_opsi, color=colors, edgecolor='grey', alpha=0.85)

ax3.set_xlabel("Dasarian Awal Masa Tanam 1 (Opsi 1 - 36)")
ax3.set_ylabel("Total Akumulasi Defisit Air Riil (mm)")
ax3.set_xticks(opsi_x)
ax3.grid(True, axis='y', alpha=0.3)

# Tandai rekomendasi terbaik (defisit terkecil)
rekomendasi_idx = np.argmin(total_defisit_36_opsi) + 1
ax3.annotate('Rekomendasi Terbaik AI', xy=(rekomendasi_idx, total_defisit_36_opsi[rekomendasi_idx-1]), 
             xytext=(rekomendasi_idx+2, total_defisit_36_opsi[rekomendasi_idx-1]+5),
             arrowprops=dict(facecolor='orange', shrink=0.05, width=2, headwidth=8))
st.pyplot(fig2)


# 5. TABEL DETAIL DATA SIMULASI
st.subheader("📋 Tabel Rincian Parameter Hidrologi & AI")
df_tabel = pd.DataFrame({
    "Fase Pertumbuhan": [f"Dasarian Ke-{i+1}" for i in range(11)],
    "Dasarian Kalender": urutan_dasarian,
    "Curah Hujan (mm)": hujan_simulasi,
    "ET0 Acuan (mm)": et0_simulasi,
    "Koefisien Kc": kc_padi,
    "ETc Tanaman (mm)": etc_simulasi,
    "Kelembaban Tanah AI (GWETROOT)": kelembaban_simulasi
})
st.dataframe(df_tabel.style.format({
    "Curah Hujan (mm)": "{:.2f}",
    "ET0 Acuan (mm)": "{:.2f}",
    "Koefisien Kc": "{:.2f}",
    "ETc Tanaman (mm)": "{:.2f}",
    "Kelembaban Tanah AI (GWETROOT)": "{:.2f}"
}), use_container_width=True)

    
# 6. KOTAK ALERT INTERAKTIF BERDASARKAN FILTER SLIDER
st.subheader("🔍 Inspeksi Titik Fase Pertumbuhan (Berdasarkan Slider)")
pilihan_fase = st.selectbox("Pilih Fase Pertumbuhan Tanaman untuk Dievaluasi:", df_tabel["Fase Pertumbuhan"])

row_pilihan = df_tabel[df_tabel["Fase Pertumbuhan"] == pilihan_fase].iloc[0]
hujan_val = row_pilihan["Curah Hujan (mm)"]
etc_val = row_pilihan["ETc Tanaman (mm)"]
gw_val = row_pilihan["Kelembaban Tanah AI (GWETROOT)"]

col1, col2 = st.columns(2)
with col1:
    st.metric(label="Neraca Air Klimatologis (Hujan - ETc)", value=f"{hujan_val - etc_val:.2f} mm")
with col2:
    st.metric(label="Status Kadar Lengas Tanah AI (GWETROOT)", value=f"{gw_val:.2f}")

# Aturan Logika Keputusan Alert Box
if hujan_val >= etc_val:
    st.success(f"🟢 **STATUS AMAN (SURPLUS):** Pasokan curah hujan mencukupi kebutuhan penguapan tanaman. Nilai kelembaban tanah terpantau optimal ({gw_val:.2f}).")
else:
    if gw_val >= 0.80:
        st.warning(f"🟡 **STATUS PERINGATAN (AMAN):** Meskipun Curah Hujan < ETc, **Tanah Masih Menyimpan Cadangan Air** yang memadai (GWETROOT = {gw_val:.2f} $\ge$ 0.80). Tanaman belum mengalami cekaman kekeringan akut berkat lengas tanah.")
    else:
        st.error(f"🔴 **STATUS KRITIS (DEFISIT RIIL):** Curah hujan tidak mencukupi dan **Kelembaban Tanah Kritis** (GWETROOT = {gw_val:.2f} < 0.80). Lahan terkonfirmasi mengalami cekaman kekeringan riil! Diperlukan tambahan air irigasi sebesar {etc_val - hujan_val:.2f} mm.")

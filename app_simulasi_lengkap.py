import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 1. SETTING LAYOUT UTAMA DASHBOARD
st.set_page_config(page_title="Simulasi Interaktif Neraca Air", layout="centered")
st.title("Simulator Kebutuhan Air Tanaman Padi Sawah Desa Nanjungan")
st.write("Geser slider untuk melihat perbandingan Kebutuhan Air ($ET_c$) dan Pasokan Curah Hujan selama 11 dasarian fase hidup tanaman.")

# 2. LOAD DATA AKTUAL HISTORIS (ET0 & HUJAN)
@st.cache_data
def load_data():
    df = pd.read_csv('dasarian_et0_hujan_data_nanjungan.csv')
    # Menghitung rata-rata ET0 dan Hujan per dasarian tahunan (1 sampai 36)
    df_grouped = df.groupby(['month', 'dasarian_num']).agg({
        'ET0_dasarian_mm_dasarian': 'mean',
        'hujan_dasarian_mm': 'mean'
    }).reset_index()
    df_grouped['dasarian_tahunan'] = range(1, 37)
    return df_grouped

df_klimatologi = load_data()

# Definisikan Kc Padi Varietas Biasa standar Nedeco/Prosida (11 Dasarian)
kc_padi = {1: 1.20, 2: 1.20, 3: 1.20, 4: 1.32, 5: 1.40, 6: 1.40, 7: 1.35, 8: 1.24, 9: 1.24, 10: 1.12, 11: 1.12}

# 3. WIDGET SLIDER DINAMIS (1 - 36)
awal_tanam = st.slider("Pilih Dasarian Awal Tanam (1-36):", min_value=1, max_value=36, value=2)

# 4. LOGIKA PERGESERAN SIKLUS HIDROLOGI
siklus_dasarian_dipilih = []
for i in range(11):
    dasarian_skrg = awal_tanam + i
    if dasarian_skrg > 36:
        dasarian_skrg = dasarian_skrg - 36
    siklus_dasarian_dipilih.append(dasarian_skrg)

et0_fase_hidup = []
hujan_fase_hidup = []
for das in siklus_dasarian_dipilih:
    row = df_klimatologi[df_klimatologi['dasarian_tahunan'] == das]
    et0_fase_hidup.append(row['ET0_dasarian_mm_dasarian'].values[0])
    hujan_fase_hidup.append(row['hujan_dasarian_mm'].values[0])

etc_fase_hidup = [et0 * kc_padi[idx+1] for idx, et0 in enumerate(et0_fase_hidup)]

# 5. RENDERING GRAFIK DENGAN UKURAN PROPORSIONAL
kolom_kiri, kolom_tengah, kolom_kanan = st.columns([0.05, 0.90, 0.05])

with kolom_tengah:
    fig, ax = plt.subplots(figsize=(8, 4), dpi=130)
    tahapan_tanam = np.arange(1, 12)

    # Plot Bar Hujan & Line ETc
    ax.bar(tahapan_tanam, hujan_fase_hidup, color='#A6C8E0', alpha=0.6, width=0.5, label='Pasokan Curah Hujan (mm/dasarian)')
    ax.plot(tahapan_tanam, etc_fase_hidup, marker='o', linewidth=2.5, color='#1F4E79', label='Kebutuhan Air Tanaman ($ET_c$)')
    ax.plot(tahapan_tanam, et0_fase_hidup, linestyle='--', linewidth=1.2, color='#8FA9C4', label='Evapotranspirasi Acuan ($ET_0$)')

    # Shading Fase Kritis Generatif
    ax.axvspan(4, 6, color='#E6EEF8', alpha=0.5, label='Fase Kritis Generatif (Pembungaan)')

    ax.set_title(f'Simulasi Neraca Air Tanaman Padi - Awal Tanam Dasarian {awal_tanam}', fontsize=11, fontweight='bold', pad=10)
    ax.set_xlabel('Tahapan Tanam (Dasarian Setelah Tanam)', fontsize=9)
    ax.set_ylabel('Volume Air (mm/dasarian)', fontsize=9)
    ax.set_xticks(tahapan_tanam)
    ax.set_xticklabels([f"{t}\n(D-{d})" for t, d in zip(tahapan_tanam, siklus_dasarian_dipilih)], fontsize=8)
    ax.grid(axis='y', linestyle=':', alpha=0.5)
    ax.legend(loc='upper right', frameon=True, facecolor='white', edgecolor='none', fontsize=8)

    st.pyplot(fig)

# ==========================================
# 6. FITUR BARU: INSPEKSI TITIK INTERAKTIF (FITUR PESANAN DOSEN)
# ==========================================
st.markdown("---")
st.subheader("🔍 Fitur Inspeksi Titik Dasarian Spesifik")

# Membuat kotak pilihan dinamis berdasarkan tahapan tanam 1-11
opsi_inspeksi = [f"Dasarian Ke-{t} Setelah Tanam (Siklus Tahunan: Dasarian {d})" for t, d in zip(tahapan_tanam, siklus_dasarian_dipilih)]
pilihan_user = st.selectbox("Pilih titik dasarian pertumbuhan yang ingin Anda periksa detailnya:", opsi_inspeksi)

# Mendapatkan indeks (0 sampai 10) dari pilihan user
indeks_terpilih = opsi_inspeksi.index(pilihan_user)

# Mengambil nilai air hujan dan ETc pada titik dasarian terpilih tersebut
hujan_titik = hujan_fase_hidup[indeks_terpilih]
etc_titik = etc_fase_hidup[indeks_terpilih]
selisih_titik = hujan_titik - etc_titik
dasarian_riil_terpilih = siklus_dasarian_dipilih[indeks_terpilih]

# Menampilkan hasil analisis dalam kotak notifikasi berwarna (Info Box)
st.write(f"**Hasil Analisis pada {pilihan_user}:**")

col_inf1, col_inf2 = st.columns(2)
with col_inf1:
    st.write(f"🔹 Pasokan Air Hujan: **{hujan_titik:.2f} mm**")
with col_inf2:
    st.write(f"🔸 Kebutuhan Air ($ET_c$): **{etc_titik:.2f} mm**")

if selisih_titik >= 0:
    st.success(f"✅ **SURPLUS AIR sebesar {abs(selisih_titik):.2f} mm** pada Dasarian {dasarian_riil_terpilih} tahunan. Pasokan curah hujan aman dan mencukupi untuk mendukung metabolisme fase ini.")
else:
    st.error(f"⚠️ **DEFISIT AIR sebesar {abs(selisih_titik):.2f} mm** pada Dasarian {dasarian_riil_terpilih} tahunan. Tanaman berisiko mengalami cekaman air jika kelembaban tanah hasil prediksi AI jatuh di bawah ambang kritis.")

# 7. METRIK RINGKAS KESELURUHAN (TOTAL 3.5 BULAN)
st.markdown("---")
st.subheader("📊 Rangkuman Total Neraca Air (Siklus 3.5 Bulan)")
total_hujan = sum(hujan_fase_hidup)
total_etc = sum(etc_fase_hidup)
defisit_neraca = total_hujan - total_etc

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Total Pasokan Air Hujan", value=f"{total_hujan:.2f} mm")
with col2:
    st.metric(label="Total Kebutuhan Air ($ET_c$)", value=f"{total_etc:.2f} mm")
with col3:
    if defisit_neraca >= 0:
        st.metric(label="Status Akhir Siklus", value="SURPLUS", delta=f"+{defisit_neraca:.2f} mm")
    else:
        st.metric(label="Status Akhir Siklus", value="DEFISIT", delta=f"{defisit_neraca:.2f} mm", delta_color="inverse")

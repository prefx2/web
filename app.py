import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import geopandas as gpd
import plotly.express as px
import os

st.set_page_config(layout="wide")

# ========== Tambahkan CSS Style
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
        background-color: #f0f4f8 !important;
        color: #1f2a40 !important;
    }
    .stApp { background-color: #f0f4f8; } 
    h1, h2, h3, h4, h5, h6 {
        color: #1f2a40 !important;
    }
    p, span, div, label {
        color: #1f2a40 !important;
        font-size: 16px !important;
    }
    section[data-testid="stSelectbox"] > label {
        color: #f0f4f8 !important;
        font-weight: 600;
        font-size: 15px !important;
        margin-bottom: 4px !important;
    }
    div[data-baseweb="select"] {
        background-color: #ccdae8 !important;
        border: 1px solid #7daae8 !important;
        border-radius: 8px !important;
        padding: 2px !important;
    }
    div[data-baseweb="select"] * {
        color: #f0f4f8 !important;
        font-size: 15px !important;
    }
    div[data-baseweb="select"] svg {
        fill: #f0f4f8 !important;
    }
    .stDownloadButton > button {
        background-color: #2c82c9;
        color: white !important;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: bold;
        border: none;
    }
    .stDownloadButton > button:hover {
        background-color: #226fa5;
        transition: background-color 0.3s ease;
    }
    div[data-testid="stInfo"],
    div[data-testid="stSuccess"],
    div[data-testid="stWarning"] {
        background-color: #e9f0f5 !important;
        border: 1px solid #d0dae5;
        border-radius: 10px;
        color: #f0f4f8 !important;
    }
    h2, h3 {
        font-weight: 600;
        color: #1f2a40 !important;
    }
    div[data-baseweb="popover"] {
    background-color: #f0f4f8 !important;
    border: 1px solid #7daae8 !important;
    border-radius: 8px !important;
    color: #f0f4f8 !important;
}

/* Item teks dalam dropdown */
div[data-baseweb="popover"] div {
    color: #f0f4f8 !important
}
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🗺️ Peta Sebaran Alat Observasi Iklim BMKG di Indonesia")

# ========== Path
base_folder = os.getcwd()
data_folder = os.path.join(base_folder, 'data')
image_folder = os.path.join(base_folder, 'image')
shapefile_folder = os.path.join(base_folder, 'shapefile')
geojson_path = os.path.join(shapefile_folder, 'zom_s_simplified.geojson')

# ========== Pilihan
col1, col2, col3 = st.columns([1.5, 1.5, 2])

with col1:
    alat_options = ['AAWS', 'ARG', 'ASRS', 'AWS', 'IKRO', 'SM']
    selected_alat = st.selectbox("🔍 Pilih Jenis Alat:", alat_options)

# Load data sesuai alat
data_path = os.path.join(data_folder, f"{selected_alat.lower()}.csv")
try:
    df = pd.read_csv(data_path, delimiter=';', encoding='utf-8', on_bad_lines='skip')
    df.columns = df.columns.str.strip()
except Exception as e:
    st.error(f"Gagal memuat data CSV: {e}")
    df = pd.DataFrame()

with col2:
    basemap_options = ['Provinsi', 'ZOM']
    selected_basemap = st.selectbox("🗺️ Pilih Basemap:", basemap_options)

with col3:
    prov_options = sorted(df['nama_propinsi'].dropna().unique()) if 'nama_propinsi' in df.columns else []
    selected_provinsi = st.selectbox("📁 Pilih Provinsi (Opsional):", ['Semua'] + prov_options)

# ========== Filter
if selected_provinsi != 'Semua':
    df_filtered = df[df['nama_propinsi'] == selected_provinsi]
else:
    df_filtered = df.copy()

# ========== Buat Peta
m = folium.Map(location=[-2.5, 118], zoom_start=5, tiles='cartodb positron')

@st.cache_resource
def load_geojson(path):
    return gpd.read_file(path)

if selected_basemap == 'ZOM':
    try:
        gdf = load_geojson(geojson_path)
        folium.GeoJson(
            gdf,
            name='ZOM',
            style_function=lambda x: {'fillColor': 'none', 'color': 'black', 'weight': 1}
        ).add_to(m)
        st.success("✅ Layer ZOM berhasil dimuat")
    except Exception as e:
        st.warning(f"Gagal memuat layer ZOM: {e}")
else:
    st.info("📌 Basemap: Provinsi")

# ========== Marker
if not df_filtered.empty and {'latt_station', 'long_station', 'name_station'}.issubset(df_filtered.columns):
    marker_cluster = MarkerCluster().add_to(m)
    for _, row in df_filtered.iterrows():
        try:
            lat = float(row['latt_station'])
            lon = float(row['long_station'])
            popup = f"""
                <b>{row['name_station']}</b><br>
                <table style="font-size: 12px;">
                  <tr><td><b>Provinsi</b></td><td>: {row.get('nama_propinsi', '')}</td></tr>
                  <tr><td><b>Kota</b></td><td>: {row.get('nama_kota', '')}</td></tr>
                  <tr><td><b>Kecamatan</b></td><td>: {row.get('kecamatan', '')}</td></tr>
                  <tr><td><b>Kelurahan</b></td><td>: {row.get('kelurahan', '')}</td></tr>
                  <tr><td><b>Latitude</b></td><td>: {lat}</td></tr>
                  <tr><td><b>Longitude</b></td><td>: {lon}</td></tr>
                </table>
            """
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup, max_width=300),
                icon=folium.Icon(color='red', icon='info-sign', icon_color='#f55442')
            ).add_to(marker_cluster)
        except:
            continue
else:
    st.info("📌 Tidak ada data untuk ditampilkan.")

folium.LayerControl().add_to(m)
st_folium(m, width=1200, height=700)

# ========== Statistik Jumlah Alat per Provinsi
jumlah = len(df_filtered)
if selected_provinsi != 'Semua':
    st.markdown(f"""
    <div style='background-color:#e9f0f5;padding:10px;border-radius:10px;margin-top:10px;'>
        <p style='color:#1f2a40; font-size:14px; margin:0;'>📍 Jumlah alat di Provinsi <b>{selected_provinsi}</b>: <span style='color:#2c82c9'>{jumlah} alat</span></p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div style='background-color:#e9f0f5;padding:10px;border-radius:10px;margin-top:10px;'>
        <p style='color:#1f2a40; font-size:14px; margin:0;'>📍 Jumlah total alat di seluruh Indonesia: <span style='color:#2c82c9'>{jumlah} alat</span></p>
    </div>
    """, unsafe_allow_html=True)
# ========== Download
st.markdown("<h2 style='color:#1f2a40;'>📥 Download Peta Statis</h2>", unsafe_allow_html=True)
nama_peta = f"{selected_alat} dengan {selected_basemap}"
st.markdown(f"<p style='color:#1f2a40; font-size:16px;'>Silakan download peta <b>{nama_peta}</b> berikut:</p>", unsafe_allow_html=True)

image_basename = f"{'zom' if selected_basemap == 'ZOM' else 'shp'}_{selected_alat}.png"
image_path = os.path.join(image_folder, image_basename)

if os.path.isfile(image_path):
    with open(image_path, "rb") as img_file:
        st.download_button(f"⬇️ Download Peta {selected_alat}", img_file, file_name=image_basename, mime="image/png")
else:
    st.warning(f"❗ Peta statis untuk {nama_peta} belum tersedia.")

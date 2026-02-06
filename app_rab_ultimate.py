import streamlit as st
import pandas as pd
import plotly.express as px
import json
import io
from datetime import datetime
from fpdf import FPDF

# ==========================================
# 1. KONFIGURASI HALAMAN & TEMA CERAH (LIGHT MODE)
# ==========================================
st.set_page_config(page_title="RAB MASTER PRO", page_icon="🏗️", layout="wide")

# CSS Custom: TEMA CERAH + FIXED TABLE
st.markdown("""
<style>
    /* Global Styles */
    .stApp {
        background-color: #ffffff; /* Putih Bersih */
        color: #2c3e50; /* Dark Blue Text */
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa; /* Light Grey */
        border-right: 1px solid #dee2e6;
    }
    
    /* Card / Metrics */
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        text-align: center;
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #3b82f6;
    }
    
    /* Expander Styling */
    .stExpander {
        background-color: #ffffff;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    
    /* Typography */
    h1, h2, h3 {
        color: #1e3a8a; /* Strong Blue */
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Data Editor / Tables */
    .stDataFrame, .stDataEditor {
        border: 1px solid #e5e7eb;
        border-radius: 6px;
    }
    
    /* Tombol */
    .stButton button {
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

def format_idr(val):
    return f"Rp {val:,.0f}".replace(",", ".")

# ==========================================
# 2. INISIALISASI DATABASE (DATABASE UTAMA)
# ==========================================
def init_state():
    # A. Identitas Proyek
    if 'project_info' not in st.session_state:
        st.session_state.project_info = {
            "name": "Pembangunan Gedung Operasional",
            "location": "Bandung, Jawa Barat",
            "year": "2025",
            "owner": "OM RIO",
            "consultant": "SMARTSTUDIO",
            "contractor": "SMARTSTUDIO KONTRAKTOR",
            "email": "smartstudio@gmail.com"
        }
    
    # B. Settings Pajak
    if 'tax_settings' not in st.session_state:
        st.session_state.tax_settings = {"profit": 10.0, "ppn": 11.0}

    # C. Database Resources (HARGA DASAR)
    # PENTING: ID disini harus sama persis dengan yang dipanggil di AHSP
    if 'resources' not in st.session_state:
        data_resources = [
            {'id': 'L.01', 'category': 'Upah', 'name': 'Pekerja', 'unit': 'OH', 'price': 107000},
            {'id': 'L.02.1', 'category': 'Upah', 'name': 'Tukang Batu', 'unit': 'OH', 'price': 110000},
            {'id': 'L.02.2', 'category': 'Upah', 'name': 'Tukang Kayu', 'unit': 'OH', 'price': 110000},
            {'id': 'L.02.3', 'category': 'Upah', 'name': 'Tukang Besi', 'unit': 'OH', 'price': 110000},
            {'id': 'L.02.4', 'category': 'Upah', 'name': 'Tukang Cat', 'unit': 'OH', 'price': 110000},
            {'id': 'L.02.5', 'category': 'Upah', 'name': 'Tukang Listrik', 'unit': 'OH', 'price': 110000},
            {'id': 'L.02.6', 'category': 'Upah', 'name': 'Tukang Pipa', 'unit': 'OH', 'price': 110000},
            {'id': 'L.02.7', 'category': 'Upah', 'name': 'Tukang Alumunium', 'unit': 'OH', 'price': 110000},
            {'id': 'L.03', 'category': 'Upah', 'name': 'Kepala Tukang', 'unit': 'OH', 'price': 120000},
            {'id': 'L.04', 'category': 'Upah', 'name': 'Mandor', 'unit': 'OH', 'price': 125000},
            # Material Sipil
            {'id': 'M.01', 'category': 'Bahan', 'name': 'Semen Portland (PC)', 'unit': 'Kg', 'price': 1516},
            {'id': 'M.01b', 'category': 'Bahan', 'name': 'Semen Mortar', 'unit': 'Kg', 'price': 2500},
            {'id': 'M.02', 'category': 'Bahan', 'name': 'Pasir Beton', 'unit': 'Kg', 'price': 1000},
            {'id': 'M.03', 'category': 'Bahan', 'name': 'Pasir Pasang', 'unit': 'M3', 'price': 132500},
            {'id': 'M.03b', 'category': 'Bahan', 'name': 'Pasir Urug', 'unit': 'M3', 'price': 90000},
            {'id': 'M.04', 'category': 'Bahan', 'name': 'Kerikil / Split', 'unit': 'Kg', 'price': 1000},
            {'id': 'M.05', 'category': 'Bahan', 'name': 'Batu Belah', 'unit': 'M3', 'price': 300000},
            {'id': 'M.06', 'category': 'Bahan', 'name': 'Bata Merah', 'unit': 'Bh', 'price': 1000},
            {'id': 'M.07', 'category': 'Bahan', 'name': 'Bata Ringan (Hebel)', 'unit': 'Bh', 'price': 8500},
            {'id': 'M.07b', 'category': 'Bahan', 'name': 'Batako', 'unit': 'Bh', 'price': 2500},
            {'id': 'M.07c', 'category': 'Bahan', 'name': 'Roster Beton', 'unit': 'Bh', 'price': 15000},
            {'id': 'M.08', 'category': 'Bahan', 'name': 'Besi Beton Polos', 'unit': 'Kg', 'price': 10900},
            {'id': 'M.09', 'category': 'Bahan', 'name': 'Kawat Beton', 'unit': 'Kg', 'price': 15000},
            {'id': 'M.10', 'category': 'Bahan', 'name': 'Paku Campur', 'unit': 'Kg', 'price': 25000},
            # Bekisting
            {'id': 'M.11', 'category': 'Bahan', 'name': 'Kayu Papan Bekisting', 'unit': 'M3', 'price': 2407000},
            {'id': 'M.12', 'category': 'Bahan', 'name': 'Kayu Kaso 5/7', 'unit': 'M3', 'price': 1800000},
            {'id': 'M.13', 'category': 'Bahan', 'name': 'Multiplek 9mm', 'unit': 'Lbr', 'price': 125000},
            {'id': 'M.14', 'category': 'Bahan', 'name': 'Minyak Bekisting', 'unit': 'Liter', 'price': 43300},
            # Arsitektur
            {'id': 'M.15', 'category': 'Bahan', 'name': 'Keramik 30x30', 'unit': 'M2', 'price': 65000},
            {'id': 'M.15b', 'category': 'Bahan', 'name': 'Keramik 40x40', 'unit': 'M2', 'price': 75000},
            {'id': 'M.15c', 'category': 'Bahan', 'name': 'Keramik 60x60', 'unit': 'M2', 'price': 120000},
            {'id': 'M.16', 'category': 'Bahan', 'name': 'Semen Warna', 'unit': 'Kg', 'price': 20000},
            {'id': 'M.17', 'category': 'Bahan', 'name': 'Cat Tembok Interior', 'unit': 'Kg', 'price': 50000},
            {'id': 'M.17b', 'category': 'Bahan', 'name': 'Cat Tembok Eksterior', 'unit': 'Kg', 'price': 75000},
            {'id': 'M.17c', 'category': 'Bahan', 'name': 'Cat Plafon', 'unit': 'Kg', 'price': 45000},
            {'id': 'M.18', 'category': 'Bahan', 'name': 'Plamir', 'unit': 'Kg', 'price': 15000},
            {'id': 'M.19', 'category': 'Bahan', 'name': 'Gypsum Board 9mm', 'unit': 'Lbr', 'price': 85000},
            {'id': 'M.20', 'category': 'Bahan', 'name': 'Hollow Galvalum 4x4', 'unit': 'Btg', 'price': 25000},
            # Atap & Pintu
            {'id': 'M.21', 'category': 'Bahan', 'name': 'Baja Ringan C75.75', 'unit': 'Btg', 'price': 75000},
            {'id': 'M.22', 'category': 'Bahan', 'name': 'Reng Baja Ringan', 'unit': 'Btg', 'price': 35000},
            {'id': 'M.23', 'category': 'Bahan', 'name': 'Atap Metal Berpasir', 'unit': 'M2', 'price': 45000},
            {'id': 'M.24', 'category': 'Bahan', 'name': 'Seng Gelombang', 'unit': 'Lbr', 'price': 50000},
            {'id': 'M.25', 'category': 'Bahan', 'name': 'Pintu UPVC Lengkap', 'unit': 'Unit', 'price': 500000},
            {'id': 'M.26', 'category': 'Bahan', 'name': 'Kusen Aluminium 4"', 'unit': 'M', 'price': 100000},
            {'id': 'M.27', 'category': 'Bahan', 'name': 'Kaca Polos 5mm', 'unit': 'M2', 'price': 120000},
            {'id': 'M.28', 'category': 'Bahan', 'name': 'Engsel Pintu', 'unit': 'Bh', 'price': 25000},
            # MEP
            {'id': 'E.01', 'category': 'Bahan', 'name': 'Kabel NYM 3x2.5mm', 'unit': 'M', 'price': 12000},
            {'id': 'E.02', 'category': 'Bahan', 'name': 'Saklar Tunggal', 'unit': 'Bh', 'price': 29000},
            {'id': 'E.03', 'category': 'Bahan', 'name': 'Stop Kontak', 'unit': 'Bh', 'price': 27200},
            {'id': 'E.04', 'category': 'Bahan', 'name': 'Lampu LED 14W', 'unit': 'Bh', 'price': 46681},
            {'id': 'E.05', 'category': 'Bahan', 'name': 'Pipa Conduit', 'unit': 'Btg', 'price': 8000},
            {'id': 'P.01', 'category': 'Bahan', 'name': 'Pipa PVC 3/4"', 'unit': 'Btg', 'price': 40000},
            {'id': 'P.02', 'category': 'Bahan', 'name': 'Pipa PVC 4"', 'unit': 'Btg', 'price': 120000},
            {'id': 'P.03', 'category': 'Bahan', 'name': 'Kloset Jongkok', 'unit': 'Bh', 'price': 500000},
        ]
        st.session_state.resources = pd.DataFrame(data_resources)

    # D. Database AHSP Master (RESEP)
    # Ini menentukan bagaimana harga dihitung dari Resources
    if 'ahsp_master' not in st.session_state:
        st.session_state.ahsp_master = {
            'AHSP.P.01': {'name': 'Pagar Sementara Seng', 'unit': 'm', 'components': [{'id': 'L.01', 'coef': 0.4}, {'id': 'L.02.2', 'coef': 0.2}, {'id': 'M.12', 'coef': 0.015}, {'id': 'M.24', 'coef': 1.2}, {'id': 'M.10', 'coef': 0.05}]},
            'AHSP.T.01': {'name': 'Galian Tanah Manual', 'unit': 'm3', 'components': [{'id': 'L.01', 'coef': 0.75}, {'id': 'L.04', 'coef': 0.025}]},
            'AHSP.S.01': {'name': 'Beton K-200 (Manual)', 'unit': 'm3', 'components': [{'id': 'L.01', 'coef': 1.65}, {'id': 'L.02.1', 'coef': 0.275}, {'id': 'M.01', 'coef': 352}, {'id': 'M.02', 'coef': 731}, {'id': 'M.04', 'coef': 1031}]},
            'AHSP.S.02': {'name': 'Pembesian Besi Polos', 'unit': 'kg', 'components': [{'id': 'L.01', 'coef': 0.007}, {'id': 'L.02.3', 'coef': 0.007}, {'id': 'M.08', 'coef': 1.05}, {'id': 'M.09', 'coef': 0.015}]},
            'AHSP.S.03': {'name': 'Pasang Bekisting', 'unit': 'm2', 'components': [{'id': 'L.01', 'coef': 0.66}, {'id': 'L.02.2', 'coef': 0.33}, {'id': 'M.11', 'coef': 0.04}, {'id': 'M.13', 'coef': 0.35}, {'id': 'M.14', 'coef': 0.1}]},
            'AHSP.S.04': {'name': 'Pondasi Batu Belah 1:5', 'unit': 'm3', 'components': [{'id': 'L.01', 'coef': 1.5}, {'id': 'L.02.1', 'coef': 0.75}, {'id': 'M.05', 'coef': 1.2}, {'id': 'M.01', 'coef': 136}, {'id': 'M.03', 'coef': 0.544}]},
            'AHSP.A.01': {'name': 'Pas. Bata Merah 1:5', 'unit': 'm2', 'components': [{'id': 'L.01', 'coef': 0.3}, {'id': 'L.02.1', 'coef': 0.1}, {'id': 'M.06', 'coef': 70}, {'id': 'M.01', 'coef': 9.68}, {'id': 'M.03', 'coef': 0.045}]},
            'AHSP.A.01b': {'name': 'Pas. Bata Ringan', 'unit': 'm2', 'components': [{'id': 'L.01', 'coef': 0.2}, {'id': 'L.02.1', 'coef': 0.1}, {'id': 'M.07', 'coef': 8.5}, {'id': 'M.01b', 'coef': 4}]},
            'AHSP.A.01c': {'name': 'Pas. Dinding Roster', 'unit': 'm2', 'components': [{'id': 'L.01', 'coef': 0.3}, {'id': 'L.02.1', 'coef': 0.15}, {'id': 'M.07c', 'coef': 25}, {'id': 'M.01', 'coef': 11}]},
            'AHSP.A.02': {'name': 'Plesteran 1:5', 'unit': 'm2', 'components': [{'id': 'L.01', 'coef': 0.3}, {'id': 'L.02.1', 'coef': 0.15}, {'id': 'M.01', 'coef': 6.24}, {'id': 'M.03', 'coef': 0.024}]},
            'AHSP.A.03': {'name': 'Acian Semen', 'unit': 'm2', 'components': [{'id': 'L.01', 'coef': 0.2}, {'id': 'L.02.1', 'coef': 0.1}, {'id': 'M.01', 'coef': 3.25}]},
            'AHSP.A.04': {'name': 'Pas. Keramik 30x30', 'unit': 'm2', 'components': [{'id': 'L.01', 'coef': 0.7}, {'id': 'L.02.1', 'coef': 0.35}, {'id': 'M.15', 'coef': 1.05}, {'id': 'M.01', 'coef': 10}, {'id': 'M.16', 'coef': 1.5}]},
            'AHSP.A.04b': {'name': 'Pas. Keramik 40x40', 'unit': 'm2', 'components': [{'id': 'L.01', 'coef': 0.65}, {'id': 'L.02.1', 'coef': 0.35}, {'id': 'M.15b', 'coef': 1.05}, {'id': 'M.01', 'coef': 10}, {'id': 'M.16', 'coef': 1.5}]},
            'AHSP.A.04c': {'name': 'Pas. Keramik 60x60', 'unit': 'm2', 'components': [{'id': 'L.01', 'coef': 0.6}, {'id': 'L.02.1', 'coef': 0.35}, {'id': 'M.15c', 'coef': 1.05}, {'id': 'M.01', 'coef': 9}, {'id': 'M.16', 'coef': 1.5}]},
            'AHSP.PL.01': {'name': 'Plafon Hollow+Gypsum', 'unit': 'm2', 'components': [{'id': 'L.02.2', 'coef': 0.35}, {'id': 'M.19', 'coef': 1.1}, {'id': 'M.20', 'coef': 3}, {'id': 'M.10', 'coef': 0.1}]},
            'AHSP.CAT.01': {'name': 'Cat Dinding Interior', 'unit': 'm2', 'components': [{'id': 'L.01', 'coef': 0.02}, {'id': 'L.02.4', 'coef': 0.063}, {'id': 'M.17', 'coef': 0.26}, {'id': 'M.18', 'coef': 0.1}]},
            'AHSP.CAT.02': {'name': 'Cat Dinding Eksterior', 'unit': 'm2', 'components': [{'id': 'L.01', 'coef': 0.03}, {'id': 'L.02.4', 'coef': 0.07}, {'id': 'M.17b', 'coef': 0.26}, {'id': 'M.18', 'coef': 0.1}]},
            'AHSP.M.01': {'name': 'Titik Lampu', 'unit': 'ttk', 'components': [{'id': 'L.01', 'coef': 0.5}, {'id': 'L.02.5', 'coef': 0.5}, {'id': 'E.01', 'coef': 12}, {'id': 'E.05', 'coef': 3}]},
            'AHSP.P.01': {'name': 'Pasang Kloset Jongkok', 'unit': 'bh', 'components': [{'id': 'L.02.1', 'coef': 1.5}, {'id': 'P.03', 'coef': 1}, {'id': 'M.01', 'coef': 6}]},
            'AHSP.P.02': {'name': 'Instalasi Air Bersih', 'unit': 'm', 'components': [{'id': 'L.02.6', 'coef': 0.15}, {'id': 'P.01', 'coef': 1.2}]},
        }

    # E. Data RAB (Hierarki: Group -> SubGroup -> Items)
    if 'rab_data' not in st.session_state:
        st.session_state.rab_data = [
            {
                "id": "A", "title": "PEKERJAAN PERSIAPAN",
                "subgroups": [
                    {
                        "id": "A.1", "title": "Pekerjaan Pembersihan",
                        "items": [
                            {"name": "Pembersihan & Kupasan Lahan", "unit": "M2", "vol": 200.0, "ahsp": None, "manual_price": 12457.5},
                            {"name": "Tebas Tebang Tanaman", "unit": "M2", "vol": 200.0, "ahsp": None, "manual_price": 3943.5},
                            {"name": "Cabut Tunggul Pohon", "unit": "Bh", "vol": 10.0, "ahsp": None, "manual_price": 152903},
                        ]
                    },
                    {
                        "id": "A.2", "title": "Pekerjaan Bongkaran",
                        "items": [
                            {"name": "Bongkaran Batu Belah", "unit": "M3", "vol": 27.0, "ahsp": None, "manual_price": 152515},
                            {"name": "Bongkar Beton Manual", "unit": "M3", "vol": 10.8, "ahsp": None, "manual_price": 168327},
                            {"name": "Bongkaran Dinding Bata", "unit": "M3", "vol": 18.0, "ahsp": None, "manual_price": 21367.5},
                            {"name": "Bongkaran Atap", "unit": "M2", "vol": 45.0, "ahsp": None, "manual_price": 13538.8},
                        ]
                    },
                    {
                        "id": "A.3", "title": "Fasilitas Sementara",
                        "items": [
                            {"name": "Pagar Seng Gelombang t=2m", "unit": "M'", "vol": 90.0, "ahsp": "AHSP.P.01", "manual_price": 0},
                            {"name": "Direksi Keet / Gudang", "unit": "M2", "vol": 15.0, "ahsp": None, "manual_price": 330678},
                            {"name": "Papan Nama Proyek", "unit": "Bh", "vol": 1.0, "ahsp": None, "manual_price": 373642},
                            {"name": "Bouwplank / Pengukuran", "unit": "M'", "vol": 95.5, "ahsp": None, "manual_price": 17782.6},
                        ]
                    }
                ]
            },
            {
                "id": "B", "title": "PEKERJAAN STRUKTUR BAWAH",
                "subgroups": [
                    {
                        "id": "B.1", "title": "Pekerjaan Tanah",
                        "items": [
                            {"name": "Galian Tanah Pondasi", "unit": "M3", "vol": 45.2, "ahsp": "AHSP.T.01", "manual_price": 0},
                            {"name": "Urukan Pasir Bawah", "unit": "M3", "vol": 5.0, "ahsp": None, "manual_price": 187500},
                            {"name": "Urukan Tanah Kembali", "unit": "M3", "vol": 15.0, "ahsp": None, "manual_price": 62287.5},
                        ]
                    },
                    {
                        "id": "B.2", "title": "Pekerjaan Pondasi",
                        "items": [
                            {"name": "Pondasi Batu Belah 1:5", "unit": "M3", "vol": 54.0, "ahsp": "AHSP.S.04", "manual_price": 0},
                            {"name": "Footplat Beton (K-200)", "unit": "M3", "vol": 15.0, "ahsp": "AHSP.S.01", "manual_price": 0},
                            {"name": "Pembesian Footplat", "unit": "Kg", "vol": 1800.0, "ahsp": "AHSP.S.02", "manual_price": 0},
                            {"name": "Sloof Beton 20x30", "unit": "M3", "vol": 9.0, "ahsp": "AHSP.S.01", "manual_price": 0},
                            {"name": "Pembesian Sloof", "unit": "Kg", "vol": 1250.0, "ahsp": "AHSP.S.02", "manual_price": 0},
                            {"name": "Bekisting Sloof", "unit": "M2", "vol": 84.4, "ahsp": "AHSP.S.03", "manual_price": 0},
                        ]
                    }
                ]
            },
            {
                "id": "C", "title": "PEKERJAAN STRUKTUR ATAS",
                "subgroups": [
                    {
                        "id": "C.1", "title": "Struktur Lantai 1",
                        "items": [
                            {"name": "Kolom K1 (40x40)", "unit": "M3", "vol": 5.6, "ahsp": "AHSP.S.01", "manual_price": 0},
                            {"name": "Bekisting Kolom K1", "unit": "M2", "vol": 63.0, "ahsp": "AHSP.S.03", "manual_price": 0},
                            {"name": "Pembesian Kolom K1", "unit": "Kg", "vol": 12557.0, "ahsp": "AHSP.S.02", "manual_price": 0},
                            {"name": "Balok B1 (30x50)", "unit": "M3", "vol": 12.0, "ahsp": "AHSP.S.01", "manual_price": 0},
                            {"name": "Bekisting Balok B1", "unit": "M2", "vol": 166.5, "ahsp": "AHSP.S.03", "manual_price": 0},
                            {"name": "Plat Lantai 2 (12cm)", "unit": "M3", "vol": 7.92, "ahsp": "AHSP.S.01", "manual_price": 0},
                        ]
                    },
                    {
                        "id": "C.2", "title": "Struktur Lantai 2 & Atap",
                        "items": [
                            {"name": "Kolom K1 Lt.2", "unit": "M3", "vol": 5.6, "ahsp": "AHSP.S.01", "manual_price": 0},
                            {"name": "Ring Balok", "unit": "M3", "vol": 19.75, "ahsp": "AHSP.S.01", "manual_price": 0},
                            {"name": "Kolom Praktis", "unit": "M3", "vol": 1.5, "ahsp": "AHSP.S.01", "manual_price": 0},
                            {"name": "Tangga Beton", "unit": "M3", "vol": 2.04, "ahsp": "AHSP.S.01", "manual_price": 0},
                            {"name": "Pembesian Str Lt.2", "unit": "Kg", "vol": 12272.0, "ahsp": "AHSP.S.02", "manual_price": 0},
                        ]
                    }
                ]
            },
            {
                "id": "D", "title": "PEKERJAAN ARSITEKTUR",
                "subgroups": [
                    {
                        "id": "D.1", "title": "Dinding",
                        "items": [
                            {"name": "Pas. Bata Merah Lt.1", "unit": "M2", "vol": 150.5, "ahsp": "AHSP.A.01", "manual_price": 0},
                            {"name": "Pas. Bata Merah Lt.2", "unit": "M2", "vol": 109.5, "ahsp": "AHSP.A.01", "manual_price": 0},
                            {"name": "Plesteran Dinding", "unit": "M2", "vol": 518.0, "ahsp": "AHSP.A.02", "manual_price": 0},
                            {"name": "Acian Dinding", "unit": "M2", "vol": 518.0, "ahsp": "AHSP.A.03", "manual_price": 0},
                            {"name": "Dinding Roster", "unit": "M2", "vol": 20.0, "ahsp": "AHSP.A.01c", "manual_price": 0},
                        ]
                    },
                    {
                        "id": "D.2", "title": "Lantai & Dinding",
                        "items": [
                            {"name": "Lantai Keramik 30x30", "unit": "M2", "vol": 85.0, "ahsp": "AHSP.A.04", "manual_price": 0},
                            {"name": "Lantai Keramik 40x40", "unit": "M2", "vol": 33.0, "ahsp": "AHSP.A.04b", "manual_price": 0},
                            {"name": "Lantai Keramik 60x60", "unit": "M2", "vol": 28.0, "ahsp": "AHSP.A.04c", "manual_price": 0},
                            {"name": "Plint Keramik", "unit": "M'", "vol": 80.0, "ahsp": None, "manual_price": 44620},
                        ]
                    },
                    {
                        "id": "D.3", "title": "Plafon",
                        "items": [
                            {"name": "Rangka+Plafon Gypsum", "unit": "M2", "vol": 92.0, "ahsp": "AHSP.PL.01", "manual_price": 0},
                            {"name": "List Plafon", "unit": "M'", "vol": 95.5, "ahsp": None, "manual_price": 18782},
                        ]
                    },
                    {
                        "id": "D.4", "title": "Pintu & Jendela",
                        "items": [
                            {"name": "Kusen Aluminium 4\"", "unit": "M'", "vol": 32.0, "ahsp": None, "manual_price": 154589},
                            {"name": "Daun Pintu UPVC", "unit": "Bh", "vol": 6.0, "ahsp": None, "manual_price": 592860},
                            {"name": "Jendela Kaca Frame Alu", "unit": "M2", "vol": 4.3, "ahsp": None, "manual_price": 327360},
                            {"name": "Kaca Polos 5mm", "unit": "M2", "vol": 20.0, "ahsp": None, "manual_price": 73183},
                            {"name": "Engsel Pintu", "unit": "Bh", "vol": 18.0, "ahsp": None, "manual_price": 44583},
                            {"name": "Kunci Tanam", "unit": "Bh", "vol": 6.0, "ahsp": None, "manual_price": 112332},
                        ]
                    },
                    {
                        "id": "D.5", "title": "Pengecatan",
                        "items": [
                            {"name": "Cat Dinding Interior", "unit": "M2", "vol": 301.0, "ahsp": "AHSP.CAT.01", "manual_price": 0},
                            {"name": "Cat Dinding Eksterior", "unit": "M2", "vol": 100.0, "ahsp": "AHSP.CAT.02", "manual_price": 0},
                            {"name": "Cat Plafon", "unit": "M2", "vol": 92.0, "ahsp": None, "manual_price": 32539},
                        ]
                    }
                ]
            },
            {
                "id": "E", "title": "MEKANIKAL & ELEKTRIKAL",
                "subgroups": [
                    {
                        "id": "E.1", "title": "Armatur Lampu",
                        "items": [
                            {"name": "Downlight 5 Inch LED", "unit": "Unit", "vol": 10.0, "ahsp": None, "manual_price": 46681.8},
                            {"name": "Fitting E27 + LED", "unit": "Unit", "vol": 25.0, "ahsp": None, "manual_price": 70881.8},
                            {"name": "Lampu Sorot LED 100W", "unit": "Unit", "vol": 2.0, "ahsp": None, "manual_price": 69132.8},
                            {"name": "Lampu Taman+Tiang", "unit": "Unit", "vol": 18.0, "ahsp": None, "manual_price": 101139},
                            {"name": "Lampu PJU Kawasan", "unit": "Unit", "vol": 18.0, "ahsp": None, "manual_price": 738614},
                        ]
                    },
                    {
                        "id": "E.2", "title": "Instalasi",
                        "items": [
                            {"name": "Instalasi Lampu", "unit": "Titik", "vol": 100.0, "ahsp": "AHSP.M.01", "manual_price": 0},
                            {"name": "Instalasi Lampu Taman", "unit": "Titik", "vol": 10.0, "ahsp": None, "manual_price": 258126},
                            {"name": "Instalasi PJU", "unit": "Titik", "vol": 4.0, "ahsp": None, "manual_price": 421476},
                        ]
                    },
                    {
                        "id": "E.3", "title": "Saklar & Stop Kontak",
                        "items": [
                            {"name": "Saklar Tunggal", "unit": "Unit", "vol": 20.0, "ahsp": None, "manual_price": 29025.7},
                            {"name": "Saklar Ganda", "unit": "Unit", "vol": 20.0, "ahsp": None, "manual_price": 29025.7},
                            {"name": "Stop Kontak", "unit": "Unit", "vol": 30.0, "ahsp": None, "manual_price": 27199.7},
                            {"name": "MCB Box", "unit": "Unit", "vol": 4.0, "ahsp": None, "manual_price": 489802},
                        ]
                    },
                    {
                        "id": "E.4", "title": "Tata Udara (AC)",
                        "items": [
                            {"name": "AC Split 1/2 PK", "unit": "Unit", "vol": 4.0, "ahsp": None, "manual_price": 871138},
                            {"name": "AC Split 1 PK", "unit": "Unit", "vol": 3.0, "ahsp": None, "manual_price": 917060},
                            {"name": "Stop Kontak AC", "unit": "Unit", "vol": 6.0, "ahsp": None, "manual_price": 37483},
                        ]
                    }
                ]
            },
            {
                "id": "F", "title": "PLUMBING & SANITAIR",
                "subgroups": [
                    {
                        "id": "F.1", "title": "Sanitair",
                        "items": [
                            {"name": "Closet Duduk", "unit": "Bh", "vol": 2.0, "ahsp": None, "manual_price": 885390},
                            {"name": "Closet Jongkok", "unit": "Bh", "vol": 1.0, "ahsp": "AHSP.P.01", "manual_price": 0},
                            {"name": "Floor Drain", "unit": "Bh", "vol": 6.0, "ahsp": None, "manual_price": 37050},
                            {"name": "Kran Air 1/2", "unit": "Bh", "vol": 10.0, "ahsp": None, "manual_price": 78960},
                            {"name": "Jet Washer", "unit": "Bh", "vol": 4.0, "ahsp": None, "manual_price": 67960},
                        ]
                    },
                    {
                        "id": "F.2", "title": "Perpipaan & Pompa",
                        "items": [
                            {"name": "Pipa PVC AW 1/2\"", "unit": "M'", "vol": 20.0, "ahsp": None, "manual_price": 37822},
                            {"name": "Pipa PVC AW 3/4\"", "unit": "M'", "vol": 10.0, "ahsp": "AHSP.P.02", "manual_price": 0},
                            {"name": "Pipa PVC D 4\" (Kotor)", "unit": "M'", "vol": 20.0, "ahsp": None, "manual_price": 89736},
                            {"name": "Pompa Transfer", "unit": "Bh", "vol": 2.0, "ahsp": None, "manual_price": 1381751},
                            {"name": "Pompa Booster", "unit": "Bh", "vol": 1.0, "ahsp": None, "manual_price": 1245424},
                            {"name": "Septictank & Resapan", "unit": "Ls", "vol": 1.0, "ahsp": None, "manual_price": 3500000},
                        ]
                    }
                ]
            }
        ]

init_state()

# ==========================================
# 4. LOGIC ENGINE (THE CALCULATOR)
# ==========================================
def calculate_ahsp_price(ahsp_id):
    """Menghitung harga satuan AHSP berdasarkan harga Resource terkini"""
    recipe = st.session_state.ahsp_master.get(ahsp_id)
    if not recipe: return 0
    
    total = 0
    # Lookup data resource dari dataframe
    res_map = {row['id']: row['price'] for row in st.session_state.resources.to_dict('records')}
    
    for comp in recipe['components']:
        price = res_map.get(comp['id'], 0)
        total += price * comp['coef']
    return total

def recalculate_totals():
    """Menghitung ulang seluruh RAB (Core Logic)"""
    grand_total_fisik = 0
    chart_data = []

    for group in st.session_state.rab_data:
        group_total = 0
        
        # Safety Check for hierarchy
        if 'subgroups' in group:
            for sub in group['subgroups']:
                sub_total = 0
                for item in sub['items']:
                    # LOGIKA UTAMA: LINKING AHSP -> HARGA SATUAN
                    # JIKA AHSP ADA DAN VALID, HITUNG. JIKA TIDAK, PAKAI MANUAL.
                    if item.get('ahsp') and item['ahsp'] in st.session_state.ahsp_master:
                        unit_price = calculate_ahsp_price(item['ahsp'])
                    else:
                        unit_price = item.get('manual_price', 0)
                    
                    # UPDATE DATA DI STATE (PENTING AGAR TIDAK 0 SAAT RENDER)
                    item['current_price'] = unit_price
                    item['total_price'] = unit_price * item['vol']
                    sub_total += item['total_price']
                
                sub['sub_total'] = sub_total
                group_total += sub_total
        
        group['group_total'] = group_total
        grand_total_fisik += group_total
        chart_data.append({"Divisi": group['title'], "Total": group_total})

    profit = grand_total_fisik * (st.session_state.tax_settings['profit'] / 100)
    subtotal = grand_total_fisik + profit
    ppn = subtotal * (st.session_state.tax_settings['ppn'] / 100)
    final_total = subtotal + ppn

    return grand_total_fisik, profit, ppn, final_total, chart_data

# === PENTING: JALANKAN KALKULASI SEBELUM RENDER UI AGAR HARGA TIDAK 0 ===
real_cost, val_profit, val_ppn, val_final, chart_data = recalculate_totals()

# ==========================================
# 5. FUNGSI UTILITAS NAVIGASI
# ==========================================
def pindah_ke_ahsp():
    st.session_state.sb_menu = "Analisa AHSP"

# ==========================================
# 6. PDF ENGINE (FPDF)
# ==========================================
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, f"REKAPITULASI RAB: {st.session_state.project_info['name'].upper()}", 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, f"Lokasi: {st.session_state.project_info['location']} | Owner: {st.session_state.project_info['owner']}", 0, 1, 'C')
        self.line(10, 30, 200, 30)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf():
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    # Header Table
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(15, 10, "NO", 1, 0, 'C', 1)
    pdf.cell(120, 10, "URAIAN PEKERJAAN", 1, 0, 'C', 1)
    pdf.cell(55, 10, "JUMLAH (Rp)", 1, 1, 'C', 1)
    
    # Body
    pdf.set_font("Arial", size=10)
    for group in st.session_state.rab_data:
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(15, 8, group['id'], 1, 0, 'C')
        pdf.cell(120, 8, group['title'], 1, 0, 'L')
        pdf.cell(55, 8, f"{group['group_total']:,.0f}", 1, 1, 'R')
        
        for sub in group['subgroups']:
            pdf.set_font("Arial", 'I', 9)
            pdf.cell(15, 6, "", 1, 0)
            pdf.cell(120, 6, f"  > {sub['title']}", 1, 0, 'L')
            pdf.cell(55, 6, f"{sub['sub_total']:,.0f}", 1, 1, 'R')

    # Footer Totals
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(135, 8, "REAL COST (FISIK)", 1, 0, 'R')
    pdf.cell(55, 8, f"{real_cost:,.0f}", 1, 1, 'R')
    pdf.cell(135, 8, f"PROFIT ({st.session_state.tax_settings['profit']}%)", 1, 0, 'R')
    pdf.cell(55, 8, f"{val_profit:,.0f}", 1, 1, 'R')
    pdf.cell(135, 8, f"PPN ({st.session_state.tax_settings['ppn']}%)", 1, 0, 'R')
    pdf.cell(55, 8, f"{val_ppn:,.0f}", 1, 1, 'R')
    
    pdf.set_fill_color(230, 240, 255)
    pdf.cell(135, 10, "GRAND TOTAL", 1, 0, 'R', 1)
    pdf.cell(55, 10, f"{val_final:,.0f}", 1, 1, 'R', 1)
    
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 7. UI LAYOUT
# ==========================================
with st.sidebar:
    st.title("🏗️ RAB MASTER")
    st.caption("Professional Edition")
    
    # State-based menu navigation agar persist
    if 'sb_menu' not in st.session_state:
        st.session_state.sb_menu = "Dashboard"
        
    menu = st.radio("Navigasi", ["Dashboard", "Rincian RAB (Input)", "Analisa AHSP", "Database Harga", "File & Laporan"], key="sb_menu")
    
    st.divider()
    st.markdown("### ⚙️ Pengaturan")
    profit_in = st.number_input("Profit (%)", value=st.session_state.tax_settings['profit'])
    ppn_in = st.number_input("PPN (%)", value=st.session_state.tax_settings['ppn'])
    
    if profit_in != st.session_state.tax_settings['profit'] or ppn_in != st.session_state.tax_settings['ppn']:
        st.session_state.tax_settings.update({"profit": profit_in, "ppn": ppn_in})
        st.rerun()

    # Grand Total Display
    st.markdown("---")
    st.markdown("<p style='font-size: 12px; color: #666;'>Total Proyek:</p>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color: #1e3a8a; margin-top: -15px;'>{format_idr(val_final)}</h2>", unsafe_allow_html=True)

# --- HALAMAN: DASHBOARD ---
if menu == "Dashboard":
    st.title("Executive Summary")
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='metric-card'><h3>Real Cost</h3><p style='font-size: 18px; font-weight: bold;'>{format_idr(real_cost)}</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><h3>Profit</h3><p style='font-size: 18px; font-weight: bold;'>{format_idr(val_profit)}</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'><h3>PPN</h3><p style='font-size: 18px; font-weight: bold;'>{format_idr(val_ppn)}</p></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='metric-card' style='border-color: #1e3a8a;'><h3>GRAND TOTAL</h3><p style='font-size: 18px; font-weight: bold; color: #1e3a8a;'>{format_idr(val_final)}</p></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("Distribusi Biaya")
        if chart_data:
            df_chart = pd.DataFrame(chart_data)
            fig = px.bar(df_chart, x='Divisi', y='Total', color='Divisi', text_auto='.2s')
            fig.update_layout(paper_bgcolor="white", plot_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
            
    with c2:
        st.subheader("Info Proyek")
        with st.container(border=True):
            st.text_input("Nama Proyek", st.session_state.project_info['name'], key="nm")
            st.text_input("Lokasi", st.session_state.project_info['location'], key="lc")
            st.text_input("Owner", st.session_state.project_info['owner'], key="ow")

# --- HALAMAN: INPUT RAB ---
elif menu == "Rincian RAB (Input)":
    st.title("Rincian Anggaran Biaya")
    
    # Tombol Pindah ke AHSP
    col_a, col_b = st.columns([3, 1])
    with col_b:
        st.button("⚙️ Kelola / Buat AHSP Baru", on_click=pindah_ke_ahsp, type="primary")
    
    st.divider()

    # Loop Groups
    for g_idx, group in enumerate(st.session_state.rab_data):
        with st.expander(f"{group['id']}. {group['title']}  |  {format_idr(group['group_total'])}", expanded=True):
            
            for s_idx, sub in enumerate(group['subgroups']):
                st.markdown(f"**{sub['id']} - {sub['title']}**")
                
                # Konversi ke DataFrame untuk Editor
                df_sub = pd.DataFrame(sub['items'])
                
                # EDITOR INTERAKTIF
                edited_df = st.data_editor(
                    df_sub,
                    column_config={
                        "name": "Uraian Pekerjaan",
                        "unit": st.column_config.SelectboxColumn("Sat", options=["M2", "M3", "Kg", "Bh", "Ls", "Titik", "Unit", "M'"], width="small"),
                        "vol": st.column_config.NumberColumn("Volume", width="small", min_value=0.0),
                        "ahsp": st.column_config.SelectboxColumn(
                            "Analisa (AHSP)", 
                            options=[None] + list(st.session_state.ahsp_master.keys()), 
                            width="medium",
                            help="Pilih Kode Analisa. Harga Satuan akan otomatis terisi."
                        ),
                        "manual_price": st.column_config.NumberColumn("Harga Manual", width="medium", help="Isi jika tidak menggunakan AHSP"),
                        "current_price": st.column_config.NumberColumn("Hrg Satuan (Auto)", disabled=True, format="Rp %d"),
                        "total_price": st.column_config.NumberColumn("Total", disabled=True, format="Rp %d")
                    },
                    use_container_width=True,
                    num_rows="dynamic",
                    key=f"editor_{group['id']}_{sub['id']}"
                )
                
                # --- LOGIKA LINKING DATA (INTI APLIKASI) ---
                if not edited_df.equals(df_sub):
                    updated_items = edited_df.to_dict('records')
                    
                    for item in updated_items:
                        # 1. Bersihkan nilai NaN pada AHSP agar dropdown tidak error
                        if pd.isna(item['ahsp']): item['ahsp'] = None
                        
                        # 2. Logic Reset Manual Price jika AHSP dipilih (Opsional, agar rapi)
                        if item['ahsp'] and item['ahsp'] in st.session_state.ahsp_master:
                            item['manual_price'] = 0 
                        
                    st.session_state.rab_data[g_idx]['subgroups'][s_idx]['items'] = updated_items
                    st.rerun() # Refresh untuk update Total Harga di UI
                # ---------------------------------------------
                st.divider()

# --- HALAMAN: DATABASE HARGA ---
elif menu == "Database Harga":
    st.title("Database Harga Dasar")
    st.info("💡 Ubah harga di sini -> AHSP update -> RAB update (Otomatis)")
    
    edited_res = st.data_editor(
        st.session_state.resources,
        column_config={
            "price": st.column_config.NumberColumn("Harga (Rp)", format="Rp %d")
        },
        use_container_width=True,
        num_rows="dynamic",
        key="res_editor"
    )
    
    if not edited_res.equals(st.session_state.resources):
        st.session_state.resources = edited_res
        st.rerun()

# --- HALAMAN: ANALISA AHSP ---
elif menu == "Analisa AHSP":
    st.title("Master Analisa (AHSP)")
    
    # 1. Menu Tambah AHSP
    with st.expander("➕ Buat Analisa Baru (Custom)", expanded=False):
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1: new_ahsp_id = st.text_input("Kode (Cth: AHSP.X.01)")
        with c2: new_ahsp_name = st.text_input("Nama Pekerjaan")
        with c3: new_ahsp_unit = st.selectbox("Satuan", ["M2", "M3", "Bh", "Ls", "Kg", "M'"])
        
        st.write("Komponen Pembentuk Harga:")
        # Template Input Komponen
        comp_template = pd.DataFrame([{"Resource_ID": "L.01", "Koefisien": 1.0}])
        all_res_ids = st.session_state.resources['id'].tolist()
        
        edited_comps = st.data_editor(
            comp_template,
            column_config={
                "Resource_ID": st.column_config.SelectboxColumn("Pilih Sumber Daya", options=all_res_ids, width="medium"),
                "Koefisien": st.column_config.NumberColumn("Koefisien", min_value=0.0, format="%.4f")
            },
            num_rows="dynamic",
            use_container_width=True,
            key="new_ahsp_maker"
        )
        
        if st.button("Simpan Analisa Baru"):
            if new_ahsp_id and new_ahsp_name and not edited_comps.empty:
                comp_list = []
                for idx, row in edited_comps.iterrows():
                    if row['Resource_ID']:
                        comp_list.append({"id": row['Resource_ID'], "coef": row['Koefisien']})
                
                st.session_state.ahsp_master[new_ahsp_id] = {
                    "name": new_ahsp_name,
                    "unit": new_ahsp_unit,
                    "components": comp_list
                }
                st.success(f"Analisa {new_ahsp_id} berhasil disimpan!")
                st.rerun()
            else:
                st.error("Data belum lengkap!")

    st.divider()

    # 2. Viewer AHSP
    sel_ahsp = st.selectbox("Lihat Detail Analisa:", list(st.session_state.ahsp_master.keys()))
    if sel_ahsp:
        dat = st.session_state.ahsp_master[sel_ahsp]
        st.subheader(f"{sel_ahsp} - {dat['name']}")
        
        comps = []
        res_map = {row['id']: row for row in st.session_state.resources.to_dict('records')}
        
        for c in dat['components']:
            r = res_map.get(c['id'])
            if r:
                comps.append({
                    "Kode": c['id'],
                    "Resource": r['name'],
                    "Koef": c['coef'],
                    "Hrg Satuan": r['price'],
                    "Total": c['coef'] * r['price']
                })
        
        df_c = pd.DataFrame(comps)
        st.dataframe(df_c, use_container_width=True)
        if not df_c.empty:
            total_analisa = df_c['Total'].sum()
            st.metric("Harga Satuan Analisa", format_idr(total_analisa))

# --- HALAMAN: FILE ---
elif menu == "File & Laporan":
    st.title("Export & Import")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Simpan Proyek")
        full_dump = {
            "project_info": st.session_state.project_info,
            "tax_settings": st.session_state.tax_settings,
            "resources": st.session_state.resources.to_dict('records'),
            "ahsp_master": st.session_state.ahsp_master,
            "rab_data": st.session_state.rab_data
        }
        json_str = json.dumps(full_dump, indent=2)
        st.download_button("💾 Download JSON Project", json_str, "rab_proyek.json", "application/json")
        
        st.write("")
        if st.button("🖨️ Generate PDF Laporan"):
            pdf_bytes = generate_pdf()
            st.download_button("📥 Unduh PDF", pdf_bytes, "Laporan_RAB.pdf", "application/pdf")
            
    with c2:
        st.subheader("Buka Proyek")
        up_file = st.file_uploader("Upload JSON", type=['json'])
        if up_file:
            try:
                d = json.load(up_file)
                st.session_state.project_info = d['project_info']
                st.session_state.tax_settings = d['tax_settings']
                st.session_state.resources = pd.DataFrame(d['resources'])
                st.session_state.ahsp_master = d['ahsp_master']
                st.session_state.rab_data = d['rab_data']
                st.success("Data berhasil dimuat!")
                st.rerun()
            except Exception as e:
                st.error(f"Gagal: {e}")

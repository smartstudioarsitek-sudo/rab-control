import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import io
import time

# ==========================================
# 1. KONFIGURASI HALAMAN & CSS (TAMPILAN GAGAH)
# ==========================================
st.set_page_config(
    page_title="RAB MASTER - Full Control System",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk meniru tampilan Dark Mode Dashboard Anda
st.markdown("""
    <style>
    .stApp {
        background-color: #0f172a;
        color: #e2e8f0;
    }
    .metric-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #1e293b;
        border-radius: 5px;
        color: white;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #2563eb;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. STATE MANAGEMENT (DATABASE)
# ==========================================
def init_session_state():
    # A. Identitas Proyek
    if 'project_info' not in st.session_state:
        st.session_state.project_info = {
            "name": "Pembangunan Gedung Operasional",
            "location": "Bandung, Jawa Barat",
            "year": "2026",
            "owner": "OM RIO",
            "consultant": "SMARTSTUDIO",
            "email": "smartstudio@gmail.com"
        }
    
    # B. Pengaturan Pajak
    if 'tax_settings' not in st.session_state:
        st.session_state.tax_settings = {
            "profit_pct": 10.0,
            "ppn_pct": 11.0
        }

    # C. Database Harga Dasar (Resources) - Sampling Data
    if 'resources' not in st.session_state:
        st.session_state.resources = pd.DataFrame([
            {'kode': 'L.01', 'nama': 'Pekerja', 'satuan': 'OH', 'kategori': 'Upah', 'harga': 107000},
            {'kode': 'L.02', 'nama': 'Tukang Batu', 'satuan': 'OH', 'kategori': 'Upah', 'harga': 110000},
            {'kode': 'M.01', 'nama': 'Semen Portland', 'satuan': 'Kg', 'kategori': 'Material', 'harga': 1516},
            {'kode': 'M.02', 'nama': 'Pasir Beton', 'satuan': 'Kg', 'kategori': 'Material', 'harga': 1000},
            {'kode': 'M.05', 'nama': 'Batu Belah', 'satuan': 'M3', 'kategori': 'Material', 'harga': 300000},
            {'kode': 'M.06', 'nama': 'Bata Merah', 'satuan': 'Bh', 'kategori': 'Material', 'harga': 1000},
        ])

    # D. Data RAB (Hierarki)
    if 'rab_data' not in st.session_state:
        st.session_state.rab_data = [
            {
                "id": "A", "title": "PEKERJAAN PERSIAPAN",
                "items": [
                    {"id": 1, "uraian": "Pembersihan Lahan", "satuan": "m2", "vol": 200.0, "harga_sat": 12457.5},
                    {"id": 2, "uraian": "Direksi Keet", "satuan": "m2", "vol": 15.0, "harga_sat": 330678.0},
                ]
            },
            {
                "id": "B", "title": "PEKERJAAN STRUKTUR",
                "items": [
                    {"id": 3, "uraian": "Galian Tanah", "satuan": "m3", "vol": 45.2, "harga_sat": 83375.0},
                    {"id": 4, "uraian": "Pondasi Batu Belah 1:5", "satuan": "m3", "vol": 54.0, "harga_sat": 881256.0},
                    {"id": 5, "uraian": "Beton Bertulang K-200", "satuan": "m3", "vol": 35.0, "harga_sat": 2502432.0},
                ]
            },
            {
                "id": "C", "title": "PEKERJAAN ARSITEKTUR",
                "items": [
                    {"id": 6, "uraian": "Pasang Dinding Bata", "satuan": "m2", "vol": 250.0, "harga_sat": 125000.0},
                    {"id": 7, "uraian": "Plesteran + Aci", "satuan": "m2", "vol": 500.0, "harga_sat": 65000.0},
                    {"id": 8, "uraian": "Cat Dinding", "satuan": "m2", "vol": 500.0, "harga_sat": 35000.0},
                ]
            },
            {
                "id": "D", "title": "MEKANIKAL & ELEKTRIKAL",
                "items": [
                     {"id": 9, "uraian": "Instalasi Titik Lampu", "satuan": "ttk", "vol": 50.0, "harga_sat": 150000.0},
                ]
            }
        ]

init_session_state()

# ==========================================
# 3. FUNGSI KALKULASI (LOGIC CORE)
# ==========================================
def calculate_totals():
    grand_total_fisik = 0
    group_summaries = []

    for group in st.session_state.rab_data:
        group_total = 0
        for item in group['items']:
            total_price = item['vol'] * item['harga_sat']
            item['total_harga'] = total_price # Update in place
            group_total += total_price
        
        group_summaries.append({
            "id": group['id'],
            "divisi": group['title'],
            "total": group_total
        })
        grand_total_fisik += group_total

    profit = grand_total_fisik * (st.session_state.tax_settings['profit_pct'] / 100)
    subtotal = grand_total_fisik + profit
    ppn = subtotal * (st.session_state.tax_settings['ppn_pct'] / 100)
    grand_total_final = subtotal + ppn

    return grand_total_fisik, profit, ppn, grand_total_final, group_summaries

# Run calculation
real_cost, val_profit, val_ppn, val_final, chart_data = calculate_totals()

# Helper Format Rupiah
def format_idr(value):
    return f"Rp {value:,.0f}".replace(",", ".")

# ==========================================
# 4. SIDEBAR MENU
# ==========================================
with st.sidebar:
    st.title("🏗️ RAB MASTER")
    st.caption("Full Control System")
    st.divider()
    
    menu = st.radio("Menu Utama", ["Dashboard", "Rincian RAB (Input)", "Harga Dasar", "Download Data"])
    
    st.divider()
    st.caption("Kontak Developer")
    st.info(f"📧 {st.session_state.project_info['email']}")
    
    st.success(f"**Total Proyek:**\n\n### {format_idr(val_final)}")

# ==========================================
# 5. MAIN CONTENT
# ==========================================

# --- PAGE: DASHBOARD ---
if menu == "Dashboard":
    st.header("Executive Summary")
    st.caption("System Live • Real-time Monitoring")
    
    # KPI Cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Real Cost (Fisik)", f"{real_cost/1e6:.1f} Jt", "Murni")
    c2.metric(f"Profit ({st.session_state.tax_settings['profit_pct']}%)", f"{val_profit/1e6:.1f} Jt", "Jasa")
    c3.metric(f"PPN ({st.session_state.tax_settings['ppn_pct']}%)", f"{val_ppn/1e6:.1f} Jt", "Pajak")
    c4.metric("GRAND TOTAL", f"{val_final/1e9:.3f} M", "Final")

    st.divider()

    # Layout: Chart & Info
    col_chart, col_info = st.columns([2, 1])
    
    with col_chart:
        st.subheader("Distribusi Biaya per Divisi")
        df_chart = pd.DataFrame(chart_data)
        fig = px.bar(df_chart, x='divisi', y='total', color='divisi', 
                     text_auto='.2s', template="plotly_dark")
        fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_info:
        st.subheader("Identitas Proyek")
        with st.container(border=True):
            st.text_input("Nama Proyek", st.session_state.project_info['name'])
            st.text_input("Lokasi", st.session_state.project_info['location'])
            st.text_input("Owner", st.session_state.project_info['owner'])
            
        st.subheader("Analisa AI")
        if st.button("✨ Analisa Kewajaran Harga"):
            with st.spinner("Mengontak Gemini AI..."):
                time.sleep(2) # Simulasi
                st.info("Analisa: Proporsi biaya Struktur (60%) wajar untuk gedung operasional. Harga satuan beton K-200 terpantau sesuai standar SNI 2025.")

# --- PAGE: INPUT RAB ---
elif menu == "Rincian RAB (Input)":
    st.header("Rincian Anggaran Biaya")
    st.caption("Mode Input Volume & Harga Satuan")

    # Accordion Style Input
    for i, group in enumerate(st.session_state.rab_data):
        group_sum = sum(item['vol'] * item['harga_sat'] for item in group['items'])
        
        with st.expander(f"{group['id']}. {group['title']}  —  {format_idr(group_sum)}", expanded=True):
            # Convert to DF for editing
            df_items = pd.DataFrame(group['items'])
            
            # Interactive Editor
            edited_df = st.data_editor(
                df_items,
                column_config={
                    "id": None, # Hide ID
                    "uraian": "Uraian Pekerjaan",
                    "satuan": st.column_config.SelectboxColumn("Sat", options=["m2", "m3", "kg", "bh", "ls", "ttk"]),
                    "vol": st.column_config.NumberColumn("Volume", format="%.2f"),
                    "harga_sat": st.column_config.NumberColumn("Harga Satuan", format="Rp %.0f"),
                    "total_harga": st.column_config.NumberColumn("Total", format="Rp %.0f", disabled=True)
                },
                use_container_width=True,
                num_rows="dynamic",
                key=f"editor_{group['id']}"
            )
            
            # Update Session State based on edits
            if not edited_df.equals(df_items):
                # Convert back to list of dicts and save
                records = edited_df.to_dict('records')
                st.session_state.rab_data[i]['items'] = records
                st.rerun()

# --- PAGE: DATABASE ---
elif menu == "Harga Dasar":
    st.header("Database Harga Satuan Dasar")
    st.caption("Analisa Harga Satuan Pekerjaan (AHSP) mengacu pada data ini.")
    
    edited_resources = st.data_editor(
        st.session_state.resources,
        column_config={
            "harga": st.column_config.NumberColumn("Harga Dasar (Rp)", format="Rp %.0f")
        },
        use_container_width=True,
        num_rows="dynamic"
    )
    
    if not edited_resources.equals(st.session_state.resources):
        st.session_state.resources = edited_resources
        st.success("Database berhasil diperbarui!")

# --- PAGE: DOWNLOAD ---
elif menu == "Download Data":
    st.header("Export Laporan")
    
    # Create Excel in Memory
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    # Sheet 1: Rekap
    df_rekap = pd.DataFrame(chart_data)
    df_rekap.to_excel(writer, sheet_name='Rekapitulasi', index=False)
    
    # Sheet 2: Detail RAB
    all_items = []
    for group in st.session_state.rab_data:
        for item in group['items']:
            item['kategori'] = group['title']
            all_items.append(item)
    df_detail = pd.DataFrame(all_items)
    df_detail.to_excel(writer, sheet_name='RAB Detail', index=False)
    
    writer.close()
    processed_data = output.getvalue()
    
    st.download_button(
        label="📥 Download Laporan Excel (.xlsx)",
        data=processed_data,
        file_name=f"RAB_{st.session_state.project_info['name']}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.json(st.session_state.rab_data, expanded=False)

# ==========================================
# FOOTER / CHATBOT AI OVERLAY (Simulasi)
# ==========================================
with st.sidebar:
    st.divider()
    st.subheader("🤖 Tanya Asisten Proyek")
    user_query = st.chat_input("Misal: Berapa harga beton K-200?")
    if user_query:
        st.write(f"**Anda:** {user_query}")
        st.write("**AI:** Berdasarkan database AHSP.S.01, harga satuan beton K-200 adalah Rp 2.502.432 per m3.")

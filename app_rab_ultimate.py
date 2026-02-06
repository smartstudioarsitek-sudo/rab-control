import streamlit as st
import pandas as pd
import plotly.express as px
import json
import io
import time
from fpdf import FPDF

# ==========================================
# 1. KONFIGURASI SISTEM & TAMPILAN
# ==========================================
st.set_page_config(
    page_title="RAB MASTER - Full Control System",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk Dark Mode Profesional
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #e2e8f0; }
    .stExpander { background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; }
    .metric-card { background-color: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #334155; }
    h1, h2, h3 { color: #f8fafc; }
    .stDataFrame { border: 1px solid #334155; }
    /* Hide Streamlit default menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def format_idr(val):
    return f"Rp {val:,.0f}".replace(",", ".")

# ==========================================
# 2. STATE MANAGEMENT (DATABASE)
# ==========================================
def init_state():
    # A. Reset Mekanisme (Pencegah Error Struktur Data Lama)
    if 'reset_trigger' not in st.session_state:
        st.session_state.reset_trigger = False

    # B. Identitas Proyek
    if 'project_info' not in st.session_state:
        st.session_state.project_info = {
            "name": "Pembangunan Gedung Operasional",
            "location": "Bandung, Jawa Barat",
            "year": "2025",
            "owner": "OM RIO",
            "consultant": "SMARTSTUDIO",
            "email": "smartstudio@gmail.com"
        }
    
    # C. Settings
    if 'tax_settings' not in st.session_state:
        st.session_state.tax_settings = {"profit": 10.0, "ppn": 11.0}

    # D. Database Sumber Daya (Resources)
    if 'resources' not in st.session_state:
        st.session_state.resources = pd.DataFrame([
            {'id': 'L.01', 'category': 'Upah', 'name': 'Pekerja', 'unit': 'OH', 'price': 107000},
            {'id': 'L.02', 'category': 'Upah', 'name': 'Tukang Batu', 'unit': 'OH', 'price': 110000},
            {'id': 'M.01', 'category': 'Bahan', 'name': 'Semen (PC)', 'unit': 'Kg', 'price': 1516},
            {'id': 'M.02', 'category': 'Bahan', 'name': 'Pasir Beton', 'unit': 'Kg', 'price': 1000},
            {'id': 'M.05', 'category': 'Bahan', 'name': 'Batu Belah', 'unit': 'M3', 'price': 300000},
            {'id': 'M.06', 'category': 'Bahan', 'name': 'Bata Merah', 'unit': 'Bh', 'price': 1000},
        ])

    # E. Database AHSP (Resep)
    if 'ahsp_master' not in st.session_state:
        st.session_state.ahsp_master = {
            "AHSP.T.01": {
                "name": "Galian Tanah Manual 1m", "unit": "M3",
                "components": [{"id": "L.01", "coef": 0.75}, {"id": "L.04", "coef": 0.025}]
            },
            "AHSP.S.04": {
                "name": "Pondasi Batu Belah 1:5", "unit": "M3",
                "components": [
                    {"id": "L.01", "coef": 1.5}, {"id": "L.02", "coef": 0.75},
                    {"id": "M.05", "coef": 1.2}, {"id": "M.01", "coef": 136}, {"id": "M.02", "coef": 544}
                ]
            }
        }

    # F. Data RAB (Hierarki: Group -> SubGroup -> Items)
    if 'rab_data' not in st.session_state:
        st.session_state.rab_data = [
            {
                "id": "A", "title": "PEKERJAAN PERSIAPAN",
                "subgroups": [
                    {
                        "id": "A.1", "title": "Pembersihan",
                        "items": [
                            {"name": "Pembersihan Lahan", "unit": "M2", "vol": 200.0, "ahsp": None, "manual_price": 12500},
                            {"name": "Direksi Keet", "unit": "M2", "vol": 15.0, "ahsp": None, "manual_price": 350000}
                        ]
                    }
                ]
            },
            {
                "id": "B", "title": "PEKERJAAN TANAH & PONDASI",
                "subgroups": [
                    {
                        "id": "B.1", "title": "Galian & Urugan",
                        "items": [
                            {"name": "Galian Tanah Pondasi", "unit": "M3", "vol": 45.2, "ahsp": "AHSP.T.01", "manual_price": 0},
                        ]
                    },
                    {
                        "id": "B.2", "title": "Pondasi",
                        "items": [
                            {"name": "Pas. Pondasi Batu Kali", "unit": "M3", "vol": 54.0, "ahsp": "AHSP.S.04", "manual_price": 0},
                        ]
                    }
                ]
            }
        ]

init_state()

# ==========================================
# 3. LOGIC ENGINE (OTAK PERHITUNGAN)
# ==========================================
def calculate_ahsp_price(ahsp_id):
    """Hitung harga satuan berdasarkan harga resource terkini"""
    recipe = st.session_state.ahsp_master.get(ahsp_id)
    if not recipe: return 0
    
    total = 0
    # Lookup harga dari DataFrame Resources
    res_df = st.session_state.resources.set_index('id')
    
    for comp in recipe['components']:
        if comp['id'] in res_df.index:
            price = res_df.loc[comp['id'], 'price']
            total += price * comp['coef']
    return total

def recalculate_totals():
    """Update seluruh total biaya RAB"""
    grand_total = 0
    chart_data = []

    for group in st.session_state.rab_data:
        group_total = 0
        for sub in group['subgroups']:
            sub_total = 0
            for item in sub['items']:
                # Tentukan Harga Satuan
                if item['ahsp'] and item['ahsp'] in st.session_state.ahsp_master:
                    unit_price = calculate_ahsp_price(item['ahsp'])
                else:
                    unit_price = item['manual_price']
                
                # Simpan hasil hitungan (bukan di database, tapi di runtime object)
                item['current_price'] = unit_price
                item['total_price'] = unit_price * item['vol']
                sub_total += item['total_price']
            
            sub['sub_total'] = sub_total
            group_total += sub_total
        
        group['group_total'] = group_total
        grand_total += group_total
        chart_data.append({"Divisi": group['title'], "Total": group_total})

    profit = grand_total * (st.session_state.tax_settings['profit'] / 100)
    ppn = (grand_total + profit) * (st.session_state.tax_settings['ppn'] / 100)
    final = grand_total + profit + ppn

    return grand_total, profit, ppn, final, chart_data

# Jalankan kalkulasi setiap rerun
real_cost, val_profit, val_ppn, val_final, chart_data = recalculate_totals()

# ==========================================
# 4. PDF ENGINE
# ==========================================
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, f"REKAPITULASI RAB: {st.session_state.project_info['name'].upper()}", 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, f"Lokasi: {st.session_state.project_info['location']} | Tahun: {st.session_state.project_info['year']}", 0, 1, 'C')
        self.line(10, 30, 200, 30)
        self.ln(10)

def generate_pdf():
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    # Table Header
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(15, 10, "NO", 1, 0, 'C', 1)
    pdf.cell(120, 10, "URAIAN PEKERJAAN", 1, 0, 'C', 1)
    pdf.cell(55, 10, "JUMLAH (Rp)", 1, 1, 'C', 1)
    
    # Content
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

    # Footer
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(135, 8, "REAL COST (FISIK)", 1, 0, 'R')
    pdf.cell(55, 8, f"{real_cost:,.0f}", 1, 1, 'R')
    pdf.cell(135, 8, f"JASA ({st.session_state.tax_settings['profit']}%)", 1, 0, 'R')
    pdf.cell(55, 8, f"{val_profit:,.0f}", 1, 1, 'R')
    pdf.cell(135, 8, f"PPN ({st.session_state.tax_settings['ppn']}%)", 1, 0, 'R')
    pdf.cell(55, 8, f"{val_ppn:,.0f}", 1, 1, 'R')
    
    pdf.set_fill_color(50, 50, 50)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(135, 10, "GRAND TOTAL", 1, 0, 'R', 1)
    pdf.cell(55, 10, f"{val_final:,.0f}", 1, 1, 'R', 1)
    
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 5. UI LAYOUT (SIDEBAR & MAIN)
# ==========================================
with st.sidebar:
    st.title("🏗️ RAB MASTER")
    st.caption("Full Control System")
    
    menu = st.radio("Navigasi", ["Dashboard", "Rincian RAB (Input)", "Analisa AHSP", "Database Harga", "File & Laporan"])
    
    st.divider()
    st.markdown("### ⚙️ Pengaturan")
    profit_in = st.number_input("Profit (%)", value=st.session_state.tax_settings['profit'])
    ppn_in = st.number_input("PPN (%)", value=st.session_state.tax_settings['ppn'])
    
    if profit_in != st.session_state.tax_settings['profit'] or ppn_in != st.session_state.tax_settings['ppn']:
        st.session_state.tax_settings.update({"profit": profit_in, "ppn": ppn_in})
        st.rerun()

    st.success(f"**Total Proyek:**\n## {format_idr(val_final)}")

# --- HALAMAN: DASHBOARD ---
if menu == "Dashboard":
    st.title("Executive Summary")
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Real Cost (Fisik)", f"{real_cost/1e6:.1f} Jt")
    col2.metric("Profit", f"{val_profit/1e6:.1f} Jt", f"{st.session_state.tax_settings['profit']}%")
    col3.metric("PPN", f"{val_ppn/1e6:.1f} Jt", f"{st.session_state.tax_settings['ppn']}%")
    col4.metric("GRAND TOTAL", f"{val_final/1e9:.3f} M")

    # Chart & Info
    c1, c2 = st.columns([2,1])
    with c1:
        st.subheader("Distribusi Biaya")
        if chart_data:
            df_chart = pd.DataFrame(chart_data)
            fig = px.bar(df_chart, x='Divisi', y='Total', color='Divisi', text_auto='.2s', template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Identitas Proyek")
        with st.container(border=True):
            st.text_input("Nama Proyek", st.session_state.project_info['name'], key="p_name")
            st.text_input("Lokasi", st.session_state.project_info['location'], key="p_loc")
            st.text_input("Owner", st.session_state.project_info['owner'], key="p_owner")

# --- HALAMAN: INPUT RAB ---
elif menu == "Rincian RAB (Input)":
    st.title("Rincian Anggaran Biaya")
    
    for g_idx, group in enumerate(st.session_state.rab_data):
        with st.expander(f"{group['id']}. {group['title']}  |  {format_idr(group['group_total'])}", expanded=True):
            for s_idx, sub in enumerate(group['subgroups']):
                st.markdown(f"**{sub['id']} - {sub['title']}**")
                
                # Konversi ke DataFrame untuk Editor
                df_sub = pd.DataFrame(sub['items'])
                
                # Editor Interaktif
                edited_df = st.data_editor(
                    df_sub,
                    column_config={
                        "name": "Uraian Pekerjaan",
                        "unit": st.column_config.SelectboxColumn("Sat", options=["M2", "M3", "KG", "BH", "LS", "TTK"], width="small"),
                        "vol": st.column_config.NumberColumn("Vol", width="small"),
                        "ahsp": st.column_config.SelectboxColumn("Analisa (AHSP)", options=[None] + list(st.session_state.ahsp_master.keys()), width="medium"),
                        "manual_price": st.column_config.NumberColumn("Harga Manual", width="medium"),
                        "current_price": st.column_config.NumberColumn("Hrg Satuan (Live)", disabled=True),
                        "total_price": st.column_config.NumberColumn("Total", disabled=True)
                    },
                    use_container_width=True,
                    num_rows="dynamic",
                    key=f"editor_{group['id']}_{sub['id']}"
                )
                
                # Simpan perubahan
                if not edited_df.equals(df_sub):
                    # Handle jika user memilih opsi kosong di dropdown AHSP
                    edited_df['ahsp'] = edited_df['ahsp'].where(pd.notnull(edited_df['ahsp']), None)
                    st.session_state.rab_data[g_idx]['subgroups'][s_idx]['items'] = edited_df.to_dict('records')
                    st.rerun()
                st.divider()

# --- HALAMAN: DATABASE HARGA ---
elif menu == "Database Harga":
    st.title("Database Harga Dasar")
    st.info("💡 Ubah harga di sini, RAB akan otomatis terupdate jika menggunakan AHSP.")
    
    edited_res = st.data_editor(
        st.session_state.resources,
        column_config={
            "price": st.column_config.NumberColumn("Harga Satuan (Rp)", format="Rp %d")
        },
        use_container_width=True,
        num_rows="dynamic",
        key="res_main_editor"
    )
    
    if not edited_res.equals(st.session_state.resources):
        st.session_state.resources = edited_res
        st.rerun()

# --- HALAMAN: FILE & LAPORAN ---
elif menu == "File & Laporan":
    st.title("Export & Import Data")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Simpan Proyek")
        # JSON DUMP
        full_data = {
            "project_info": st.session_state.project_info,
            "tax_settings": st.session_state.tax_settings,
            "resources": st.session_state.resources.to_dict('records'),
            "ahsp_master": st.session_state.ahsp_master,
            "rab_data": st.session_state.rab_data
        }
        json_str = json.dumps(full_data, indent=2)
        st.download_button("💾 Download JSON Proyek", json_str, file_name="rab_proyek.json", mime="application/json")
        
        # PDF GENERATE
        st.write("")
        if st.button("🖨️ Generate PDF Laporan"):
            pdf_bytes = generate_pdf()
            st.download_button("📥 Download PDF Siap Cetak", pdf_bytes, file_name="Laporan_RAB.pdf", mime="application/pdf")
            
    with col_b:
        st.subheader("Buka Proyek")
        uploaded_file = st.file_uploader("Upload file .json", type=["json"])
        if uploaded_file:
            try:
                data = json.load(uploaded_file)
                st.session_state.project_info = data['project_info']
                st.session_state.tax_settings = data['tax_settings']
                st.session_state.resources = pd.DataFrame(data['resources'])
                st.session_state.ahsp_master = data['ahsp_master']
                st.session_state.rab_data = data['rab_data']
                st.success("Data berhasil dimuat!")
                st.rerun()
            except Exception as e:
                st.error(f"Gagal memuat file: {e}")

# --- AI CHATBOT OVERLAY ---
with st.expander("💬 Tanya Asisten Konstruksi (AI)", expanded=False):
    st.chat_message("assistant").write("Halo! Saya siap bantu hitung volume atau analisa harga.")
    prompt = st.chat_input("Tanya sesuatu...")
    if prompt:
        st.chat_message("user").write(prompt)
        # Placeholder untuk integrasi API Gemini
        st.chat_message("assistant").write("Fitur AI akan aktif jika API Key disematkan. (Mode Demo)")

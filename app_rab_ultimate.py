import streamlit as st
import pandas as pd
import plotly.express as px
import json
import io
from datetime import datetime
from fpdf import FPDF

# ==========================================
# 1. KONFIGURASI SISTEM & UTILITAS
# ==========================================
st.set_page_config(page_title="RAB MASTER ULTIMATE", page_icon="🏗️", layout="wide")

# CSS Kustom untuk Tampilan Pro
st.markdown("""
<style>
    .main { background-color: #0f172a; color: #e2e8f0; }
    .stExpander { background-color: #1e293b; border-radius: 8px; border: 1px solid #334155; }
    .metric-card { padding: 15px; border-radius: 10px; border: 1px solid #334155; background: #1e293b; }
    h1, h2, h3 { color: #fff; }
    .stDataFrame { border: 1px solid #334155; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

def format_idr(val):
    return f"Rp {val:,.0f}".replace(",", ".")

# ==========================================
# 2. INISIALISASI DATA (SESSION STATE)
# ==========================================
def init_state():
    if 'project_info' not in st.session_state:
        st.session_state.project_info = {
            "name": "Pembangunan Gedung Operasional",
            "owner": "OM RIO",
            "loc": "Bandung",
            "year": "2026",
            "consultant": "SMARTSTUDIO"
        }
    
    if 'settings' not in st.session_state:
        st.session_state.settings = {"profit": 10.0, "ppn": 11.0}

    # DATABASE SUMBER DAYA (Resources)
    if 'resources' not in st.session_state:
        st.session_state.resources = pd.DataFrame([
            {'id': 'L.01', 'name': 'Pekerja', 'unit': 'OH', 'price': 107000, 'type': 'Upah'},
            {'id': 'L.02', 'name': 'Tukang Batu', 'unit': 'OH', 'price': 110000, 'type': 'Upah'},
            {'id': 'M.01', 'name': 'Semen (PC)', 'unit': 'Kg', 'price': 1516, 'type': 'Material'},
            {'id': 'M.02', 'name': 'Pasir Beton', 'unit': 'Kg', 'price': 1000, 'type': 'Material'},
            {'id': 'M.05', 'name': 'Batu Belah', 'unit': 'M3', 'price': 300000, 'type': 'Material'},
        ])

    # DATABASE ANALISA (AHSP Recipes)
    if 'ahsp_master' not in st.session_state:
        st.session_state.ahsp_master = {
            "AHSP.T.01": {
                "name": "Galian Tanah Manual 1m",
                "unit": "M3",
                "components": [{"id": "L.01", "coef": 0.75}, {"id": "L.04", "coef": 0.025}]
            },
            "AHSP.S.04": {
                "name": "Pondasi Batu Belah 1:5",
                "unit": "M3",
                "components": [
                    {"id": "L.01", "coef": 1.5}, 
                    {"id": "L.02", "coef": 0.75},
                    {"id": "M.05", "coef": 1.2},
                    {"id": "M.01", "coef": 136},
                    {"id": "M.02", "coef": 544} # Konversi ke Kg
                ]
            }
        }

    # DATA RAB (HIERARKI: Group -> SubGroup -> Items)
    if 'rab_data' not in st.session_state:
        st.session_state.rab_data = [
            {
                "id": "A", "title": "PEKERJAAN PERSIAPAN",
                "subgroups": [
                    {
                        "id": "A.1", "title": "Pembersihan",
                        "items": [
                            {"id": 101, "name": "Pembersihan Lahan", "unit": "M2", "vol": 200.0, "ahsp": None, "manual_price": 12500},
                            {"id": 102, "name": "Direksi Keet", "unit": "M2", "vol": 15.0, "ahsp": None, "manual_price": 350000}
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
                            {"id": 201, "name": "Galian Tanah Pondasi", "unit": "M3", "vol": 45.2, "ahsp": "AHSP.T.01", "manual_price": 0},
                        ]
                    },
                    {
                        "id": "B.2", "title": "Pondasi",
                        "items": [
                            {"id": 202, "name": "Pas. Pondasi Batu Kali", "unit": "M3", "vol": 54.0, "ahsp": "AHSP.S.04", "manual_price": 0},
                        ]
                    }
                ]
            }
        ]

init_state()

# ==========================================
# 3. LOGIC ENGINE (OTAK GEMS)
# ==========================================
def calculate_ahsp_price(ahsp_id):
    """Menghitung harga satuan berdasarkan harga resource terkini"""
    recipe = st.session_state.ahsp_master.get(ahsp_id)
    if not recipe: return 0
    
    total = 0
    for comp in recipe['components']:
        res = st.session_state.resources[st.session_state.resources['id'] == comp['id']]
        if not res.empty:
            price = res.iloc[0]['price']
            total += price * comp['coef']
    return total

def recalculate_rab():
    """Mengupdate seluruh harga RAB"""
    grand_total = 0
    chart_data = []
    
    # Update Resource Map for fast lookup
    # (Sudah dihandle di calculate_ahsp_price via dataframe filtering)

    for group in st.session_state.rab_data:
        group_total = 0
        for sub in group['subgroups']:
            sub_total = 0
            for item in sub['items']:
                # Tentukan Harga Satuan (AHSP vs Manual)
                if item['ahsp']:
                    unit_price = calculate_ahsp_price(item['ahsp'])
                else:
                    unit_price = item['manual_price']
                
                # Simpan harga terkini ke item (untuk display)
                item['current_price'] = unit_price 
                item['total_price'] = unit_price * item['vol']
                
                sub_total += item['total_price']
            
            sub['sub_total'] = sub_total
            group_total += sub_total
        
        group['group_total'] = group_total
        grand_total += group_total
        chart_data.append({"Divisi": group['title'], "Total": group_total})
    
    profit = grand_total * (st.session_state.settings['profit'] / 100)
    ppn = (grand_total + profit) * (st.session_state.settings['ppn'] / 100)
    final_total = grand_total + profit + ppn
    
    return grand_total, profit, ppn, final_total, chart_data

# Jalankan kalkulasi setiap rerun
real_cost, val_profit, val_ppn, val_final, chart_data = recalculate_rab()

# ==========================================
# 4. PDF GENERATOR ENGINE
# ==========================================
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, f"REKAPITULASI RAB: {st.session_state.project_info['name'].upper()}", 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, f"Pemilik: {st.session_state.project_info['owner']} | Tahun: {st.session_state.project_info['year']}", 0, 1, 'C')
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
    
    # Table Header
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(15, 10, "NO", 1, 0, 'C', 1)
    pdf.cell(120, 10, "URAIAN PEKERJAAN", 1, 0, 'C', 1)
    pdf.cell(55, 10, "JUMLAH HARGA (Rp)", 1, 1, 'C', 1)
    
    # Content
    pdf.set_font("Arial", size=10)
    for group in st.session_state.rab_data:
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(15, 8, group['id'], 1, 0, 'C')
        pdf.cell(120, 8, group['title'], 1, 0, 'L')
        pdf.cell(55, 8, f"{group['group_total']:,.0f}", 1, 1, 'R')
        
        for sub in group['subgroups']:
            pdf.set_font("Arial", 'I', 9)
            pdf.cell(15, 7, "", 1, 0)
            pdf.cell(120, 7, f"  > {sub['title']}", 1, 0, 'L')
            pdf.cell(55, 7, f"{sub['sub_total']:,.0f}", 1, 1, 'R')

    # Footer Totals
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(135, 8, "REAL COST (FISIK)", 1, 0, 'R')
    pdf.cell(55, 8, f"{real_cost:,.0f}", 1, 1, 'R')
    pdf.cell(135, 8, f"JASA ({st.session_state.settings['profit']}%)", 1, 0, 'R')
    pdf.cell(55, 8, f"{val_profit:,.0f}", 1, 1, 'R')
    pdf.cell(135, 8, f"PPN ({st.session_state.settings['ppn']}%)", 1, 0, 'R')
    pdf.cell(55, 8, f"{val_ppn:,.0f}", 1, 1, 'R')
    
    pdf.set_fill_color(50, 50, 50)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(135, 10, "GRAND TOTAL PROYEK", 1, 0, 'R', 1)
    pdf.cell(55, 10, f"{val_final:,.0f}", 1, 1, 'R', 1)
    
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 5. UI LAYOUT
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2910/2910795.png", width=50)
    st.title("RAB MASTER")
    st.caption("Ultimate Python Edition")
    
    tab_nav = st.radio("Navigasi", ["📊 Dashboard", "📝 Input RAB", "🧱 Analisa AHSP", "💰 Sumber Daya", "📂 File & PDF"])
    
    st.divider()
    st.markdown("### ⚙️ Global Settings")
    profit_in = st.number_input("Profit (%)", value=st.session_state.settings['profit'])
    ppn_in = st.number_input("PPN (%)", value=st.session_state.settings['ppn'])
    
    if profit_in != st.session_state.settings['profit'] or ppn_in != st.session_state.settings['ppn']:
        st.session_state.settings['profit'] = profit_in
        st.session_state.settings['ppn'] = ppn_in
        st.rerun()

# --- TAB 1: DASHBOARD ---
if "Dashboard" in tab_nav:
    st.title("Executive Summary")
    
    # Kartu KPI
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Real Cost", f"{real_cost/1e6:.1f} Jt", "Fisik Murni")
    k2.metric("Jasa Konstruksi", f"{val_profit/1e6:.1f} Jt", f"{st.session_state.settings['profit']}%")
    k3.metric("Pajak (PPN)", f"{val_ppn/1e6:.1f} Jt", f"{st.session_state.settings['ppn']}%")
    k4.metric("GRAND TOTAL", f"{val_final/1e9:.3f} M", "Final")
    
    # Grafik & Info
    c_left, c_right = st.columns([2, 1])
    with c_left:
        st.subheader("Distribusi Anggaran")
        if chart_data:
            df_chart = pd.DataFrame(chart_data)
            fig = px.bar(df_chart, x='Divisi', y='Total', text_auto='.2s', color='Divisi')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Belum ada data RAB.")
            
    with c_right:
        st.subheader("Info Proyek")
        with st.container(border=True):
            st.text_input("Nama Proyek", st.session_state.project_info['name'])
            st.text_input("Lokasi", st.session_state.project_info['loc'])
            st.text_input("Pemilik", st.session_state.project_info['owner'])

# --- TAB 2: INPUT RAB (NESTED) ---
elif "Input RAB" in tab_nav:
    st.title("Rincian Anggaran Biaya")
    
    # Loop Group (Divisi)
    for g_idx, group in enumerate(st.session_state.rab_data):
        with st.expander(f"{group['id']}. {group['title']}  |  {format_idr(group['group_total'])}", expanded=True):
            
            # Loop Subgroup
            for s_idx, sub in enumerate(group['subgroups']):
                st.markdown(f"**{sub['id']} - {sub['title']}**")
                
                # Kita gunakan data editor untuk tiap subgroup
                df_sub = pd.DataFrame(sub['items'])
                
                # Config Editor
                edited_df = st.data_editor(
                    df_sub,
                    column_config={
                        "id": None, 
                        "name": "Uraian Pekerjaan",
                        "unit": st.column_config.SelectboxColumn("Sat", options=["M2", "M3", "KG", "BH", "LS", "TTK"], width="small"),
                        "vol": st.column_config.NumberColumn("Volume", width="small"),
                        "ahsp": st.column_config.SelectboxColumn("Analisa (AHSP)", options=[None] + list(st.session_state.ahsp_master.keys()), width="medium"),
                        "manual_price": st.column_config.NumberColumn("Harga Manual", width="medium"),
                        "current_price": st.column_config.NumberColumn("Hrg Satuan (Live)", disabled=True),
                        "total_price": st.column_config.NumberColumn("Total", disabled=True)
                    },
                    key=f"editor_{group['id']}_{sub['id']}",
                    use_container_width=True,
                    num_rows="dynamic"
                )
                
                # Simpan perubahan
                if not edited_df.equals(df_sub):
                    # Convert NaN ahsp to None
                    edited_df['ahsp'] = edited_df['ahsp'].where(pd.notnull(edited_df['ahsp']), None)
                    st.session_state.rab_data[g_idx]['subgroups'][s_idx]['items'] = edited_df.to_dict('records')
                    st.rerun()
                
                st.divider()

# --- TAB 3: SUMBER DAYA (RESOURCES) ---
elif "Sumber Daya" in tab_nav:
    st.title("Database Harga Dasar")
    st.info("Mengubah harga di sini akan otomatis mengupdate RAB yang menggunakan AHSP terkait.")
    
    edited_res = st.data_editor(
        st.session_state.resources,
        column_config={
            "price": st.column_config.NumberColumn("Harga Satuan (Rp)", format="Rp %d")
        },
        use_container_width=True,
        num_rows="dynamic",
        key="res_editor"
    )
    
    if not edited_res.equals(st.session_state.resources):
        st.session_state.resources = edited_res
        st.rerun()

# --- TAB 4: ANALISA AHSP ---
elif "Analisa AHSP" in tab_nav:
    st.title("Master Analisa (AHSP)")
    
    selected_ahsp = st.selectbox("Pilih Kode Analisa", list(st.session_state.ahsp_master.keys()))
    
    if selected_ahsp:
        data = st.session_state.ahsp_master[selected_ahsp]
        st.subheader(f"{selected_ahsp} - {data['name']}")
        
        # Tampilkan Komponen
        st.write("Komponen Pembentuk Harga:")
        comps = []
        for c in data['components']:
            res_row = st.session_state.resources[st.session_state.resources['id'] == c['id']]
            if not res_row.empty:
                r = res_row.iloc[0]
                comps.append({
                    "Kode": c['id'],
                    "Nama": r['name'],
                    "Koefisien": c['coef'],
                    "Hrg Satuan": r['price'],
                    "Sub Total": c['coef'] * r['price']
                })
        
        df_comp = pd.DataFrame(comps)
        st.dataframe(df_comp, use_container_width=True)
        st.markdown(f"### Harga Satuan Analisa: {format_idr(df_comp['Sub Total'].sum())} /{data['unit']}")

# --- TAB 5: FILE & EXPORT ---
elif "File" in tab_nav:
    st.title("Manajemen File")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("💾 Simpan Data")
        # Export JSON
        full_data = {
            "project_info": st.session_state.project_info,
            "settings": st.session_state.settings,
            "resources": st.session_state.resources.to_dict('records'),
            "ahsp_master": st.session_state.ahsp_master,
            "rab_data": st.session_state.rab_data
        }
        json_str = json.dumps(full_data, indent=2)
        st.download_button("Download JSON Project", json_str, file_name="proyek_rab.json", mime="application/json")
        
        # Export PDF
        st.subheader("🖨️ Cetak Laporan")
        if st.button("Generate PDF Laporan"):
            pdf_bytes = generate_pdf()
            st.download_button(
                label="Download PDF Ready Print",
                data=pdf_bytes,
                file_name="Laporan_RAB.pdf",
                mime="application/pdf"
            )

    with c2:
        st.subheader("📂 Buka Data")
        uploaded_file = st.file_uploader("Upload file .json proyek", type=["json"])
        if uploaded_file:
            try:
                data = json.load(uploaded_file)
                st.session_state.project_info = data['project_info']
                st.session_state.settings = data['settings']
                st.session_state.resources = pd.DataFrame(data['resources'])
                st.session_state.ahsp_master = data['ahsp_master']
                st.session_state.rab_data = data['rab_data']
                st.success("Data berhasil dimuat!")
                st.rerun()
            except Exception as e:
                st.error(f"File rusak: {e}")

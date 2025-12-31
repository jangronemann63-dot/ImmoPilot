import streamlit as st
import pandas as pd
import time
import os
from pypdf import PdfReader 
from fpdf import FPDF
from auth import init_db, authenticate_user, initiate_registration, verify_user_code, save_to_watchlist, get_user_watchlist, delete_from_watchlist, update_watchlist_entry
from logic import (
    fetch_listings_from_url, 
    run_triage_analyst, 
    run_deep_dive_analyst, 
    generate_bank_expose, 
    get_available_models,
    GRUNDERWERBSTEUER
)

# --- CONFIG ---
st.set_page_config(page_title="ImmoPilot AI", page_icon="🏢", layout="wide")
init_db()

# Session States
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "user_email" not in st.session_state: st.session_state.user_email = None

# Styles
# HIER WURDE KORRIGIERT: Höhe auf 3rem reduziert und angeglichen
st.markdown("""
<style>
    /* Styling für Buttons */
    .stButton>button {
        height: 3rem;              /* Standardhöhe, passend zum Input */
        border-radius: 8px;       
        font-size: 16px !important; 
        font-weight: 600;
        border: none;
    }
    
    /* Styling für Text-Inputs (URL Feld) */
    .stTextInput>div>div>input {
        height: 3rem;              /* Exakt gleiche Höhe wie Button */
        border-radius: 8px;
        font-size: 16px;
    }

    /* Layout Anpassungen */
    .block-container {padding-top: 2rem;}
    [data-testid="stImage"] {margin-bottom: -10px;}
</style>
""", unsafe_allow_html=True)


# ==========================================
# 📄 PDF GENERATOR KLASSE (DESIGN UPGRADE)
# ==========================================
class PDF(FPDF):
    def header(self):
        # Corporate Identity Colors (Dunkles Blau/Schwarz aus deiner App)
        self.set_fill_color(24, 26, 32) # Dark Background wie im Web
        self.rect(0, 0, 210, 40, 'F')
        
        # Logo (falls vorhanden)
        logo_path = r"C:\Users\Jan-P\Desktop\POC\Logo\Logo.jpg"
        if os.path.exists(logo_path):
            try:
                self.image(logo_path, 170, 8, 25) 
            except: pass
            
        self.set_font('Arial', 'B', 20)
        self.set_text_color(255, 255, 255) # Weißer Text
        self.set_xy(15, 12)
        self.cell(0, 10, 'Investitions-Memorandum', 0, 0, 'L')
        
        self.set_font('Arial', '', 10)
        self.set_text_color(200, 200, 200) # Helles Grau
        self.set_xy(15, 22)
        self.cell(0, 10, 'Vertrauliche Finanzierungsanfrage | ImmoPilot AI', 0, 0, 'L')
        self.ln(35) # Abstand zum Body

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Seite {self.page_no()} | Erstellt mit ImmoPilot AI', 0, 0, 'C')

    def chapter_title(self, label):
        # Überschriften im App-Look (Rot/Orange Akzent)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(255, 75, 75) # Dein "Button-Rot"
        self.cell(0, 10, label, 0, 1, 'L')
        self.ln(2)

    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 6, body)
        self.ln()

    def draw_table(self, table_lines):
        # Tabellen-Parser & Renderer
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(240, 240, 240) # Hellgrau für Header
        self.set_draw_color(200, 200, 200) # Graue Linien
        self.set_text_color(0)
        
        # Daten parsen
        parsed_data = []
        for line in table_lines:
            # Entferne äußere Pipes und splitte
            clean_line = line.strip().strip('|')
            cols = [c.strip() for c in clean_line.split('|')]
            if "---" in cols[0]: continue # Trennlinien ignorieren
            parsed_data.append(cols)

        if not parsed_data: return

        # Spaltenbreiten berechnen (dynamisch)
        num_cols = len(parsed_data[0])
        page_width = 190 # A4 minus Ränder
        col_width = page_width / num_cols
        
        # Header zeichnen
        for col in parsed_data[0]:
            self.cell(col_width, 8, col, 1, 0, 'C', True)
        self.ln()
        
        # Body zeichnen
        self.set_font('Arial', '', 10)
        self.set_fill_color(255, 255, 255)
        
        for row in parsed_data[1:]:
            for col in row:
                # Prüfen ob Zahl (rechtsbündig) oder Text (linksbündig)
                align = 'R' if any(c.isdigit() for c in col) and "€" in col else 'L'
                # Bold für "Gesamt" Zeilen
                if "Gesamt" in col or "**" in col:
                    self.set_font('Arial', 'B', 10)
                    col = col.replace("**", "")
                else:
                    self.set_font('Arial', '', 10)
                    
                self.cell(col_width, 8, col, 1, 0, align)
            self.ln()
        self.ln(5)

def create_pdf(text_content, user_email):
    pdf = PDF()
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    pdf.add_page()
    
    # Meta-Info Zeile
    pdf.set_font("Arial", "", 10)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(0, 10, f"  Antragsteller: {user_email}  |  Datum: {time.strftime('%d.%m.%Y')}", 0, 1, 'L', True)
    pdf.ln(5)

    # Text Zeilenweise verarbeiten
    clean_text = text_content.replace("€", "EUR").replace("–", "-")
    lines = clean_text.split('\n')
    
    buffer_table = []
    in_table = False
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_table: # Tabelle zu Ende -> Zeichnen
                pdf.draw_table(buffer_table)
                buffer_table = []
                in_table = False
            pdf.ln(2)
            continue
            
        # Tabellen-Erkennung (Zeile beginnt und endet mit |)
        if line.startswith("|") and line.endswith("|"):
            in_table = True
            buffer_table.append(line)
            continue
        
        # Falls Tabelle gerade vorbei war
        if in_table:
            pdf.draw_table(buffer_table)
            buffer_table = []
            in_table = False

        # Überschriften (#)
        if line.startswith("#"):
            clean_line = line.replace("#", "").strip()
            pdf.chapter_title(clean_line)
        # Bold Text (**)
        elif line.startswith("**") and line.endswith("**"):
             pdf.set_font("Arial", "B", 11)
             pdf.cell(0, 6, line.replace("**", ""), 0, 1)
        # Normaler Text
        else:
            pdf.set_font("Arial", "", 11)
            pdf.multi_cell(0, 6, line)

    # Falls am Ende noch eine Tabelle offen ist
    if in_table:
        pdf.draw_table(buffer_table)
            
    return pdf.output(dest='S').encode('latin-1', 'replace')
# ==========================================
# 🔐 LOGIN
# ==========================================
if not st.session_state.authenticated:
    try: st.image(r"C:\Users\Jan-P\Desktop\POC\Logo\Logo.jpg", width=250)
    except: st.header("🏢 ImmoPilot AI")
    st.divider()
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        tab1, tab2 = st.tabs(["Login", "Registrieren"])
        with tab1:
            e = st.text_input("Email", key="l_e"); p = st.text_input("Passwort", type="password", key="l_p")
            if st.button("Login", use_container_width=True):
                s, m = authenticate_user(e, p)
                if s: st.session_state.authenticated=True; st.session_state.user_email=e; st.rerun()
                else: st.error(m)
        with tab2:
            e_r = st.text_input("Email", key="r_e"); p_r = st.text_input("Passwort", type="password", key="r_p")
            if st.button("Code anfordern"):
                s, m = initiate_registration(e_r, p_r)
                if s: st.session_state.tmp_email=e_r; st.info(m)
                else: st.error(m)
            if "tmp_email" in st.session_state:
                code = st.text_input("Code")
                if st.button("Prüfen"):
                    s, m = verify_user_code(st.session_state.tmp_email, code)
                    if s: st.success(m); time.sleep(1); st.session_state.reg_step=1; st.rerun()
                    else: st.error(m)
    st.stop()

# ==========================================
# 🚀 APP
# ==========================================
with st.sidebar:
    st.write(f"👤 **{st.session_state.user_email}**")
    page = st.radio("Navigation", ["🔍 Neue Suche", "📂 Meine Watchlist"], index=0)
    st.divider()
    if st.button("Ausloggen", type="secondary"):
        st.session_state.authenticated = False; st.session_state.user_email = None; st.rerun()

    if page == "🔍 Neue Suche" or page == "📂 Meine Watchlist":
        with st.expander("💰 Profil-Daten", expanded=(page=="🔍 Neue Suche")):
            user_net_income = st.number_input("Netto (€)", 0, 50000, 4000, step=500)
            user_assets = st.number_input("Vermögen (€)", 0, 5000000, 100000, step=10000)
            st.divider()
            user_ek = st.number_input("Eigenkapital (€)", 0, 1000000, 50000, step=5000)
            selected_state = st.selectbox("Bundesland", sorted(list(GRUNDERWERBSTEUER.keys())), index=10)
            user_tax = st.slider("Steuer (%)", 20, 50, 42)
            user_makler_perc = st.number_input("Makler (%)", 0.0, 10.0, 3.57, step=0.1)
            user_zins = st.slider("Zins (%)", 1.0, 6.0, 3.8, step=0.1)
            user_sanierung = st.number_input("Sanierung (€)", 0, 100000, 5000, step=1000)
        selected_model = st.selectbox("KI-Modell:", get_available_models(), index=0)

    user_profile = {
        "ek": user_ek if 'user_ek' in locals() else 50000, 
        "zins": user_zins if 'user_zins' in locals() else 3.8, 
        "tax": user_tax if 'user_tax' in locals() else 42,
        "sanierung": user_sanierung if 'user_sanierung' in locals() else 5000, 
        "makler_prozent": user_makler_perc if 'user_makler_perc' in locals() else 3.57,
        "bundesland": selected_state if 'selected_state' in locals() else "Nordrhein-Westfalen", 
        "net_income": user_net_income if 'user_net_income' in locals() else 4000, 
        "assets": user_assets if 'user_assets' in locals() else 100000
    }

# --- PAGE 1: SUCHE ---
if page == "🔍 Neue Suche":
    try: st.image(r"C:\Users\Jan-P\Desktop\POC\Logo\Logo.jpg", width=300)
    except: st.header("ImmoPilot AI")
    
    with st.expander("📖 So nutzt du den ImmoPilot (Hier klicken)", expanded=False):
        st.markdown("""
        Das Tool nutzt Live-Daten von Plattformen wie eBay Kleinanzeigen und bewertet diese direkt mit KI, um dir die lästige Arbeit des Suchens abzunehmen.
        
        **1. Profil einstellen (WICHTIG!)**
        Öffne links die Sidebar **"💰 Profil-Daten"**. Die KI braucht dein Eigenkapital & Gehalt, um deinen persönlichen Cashflow zu berechnen.
        
        **2. Suchen & Scannen**
        Kopiere eine Such-URL von *eBay Kleinanzeigen* und füge sie unten ein. Klicke auf **🚀 Scan**.
        Die KI bewertet Objekte von **1 (Schlecht)** bis **10 (Top Investment)**.
        
        **3. Vorprüfung (Lohnt sich der Aufwand?)**
        Wähle ein Objekt aus und klicke auf **✨ Schneller Deep-Dive**.
        * **Ergebnis gut?** -> Speichere das Objekt in der Watchlist und fordere das Exposé an.
        
        **4. Akten-Check & Bank (Watchlist)**
        Sobald du Unterlagen hast: Lade in der *Watchlist* die **PDFs** hoch. Die KI prüft diese auf versteckte Kosten. Erst danach erstellst du dort das **Bank-Exposé**.
        """)
        st.info("💡 **Tipp:** Nutze die Suche von eBay Kleinanzeigen (z. B. Wohnungen bis 150.000 €), um die Liste vorzufiltern.")
    
    # HIER WURDE KORRIGIERT: vertical_alignment="bottom" sorgt dafür, dass Button und Input auf einer Linie liegen
    c1, c2 = st.columns([4, 1], vertical_alignment="bottom")
    
    # Label visibility collapsed, damit es keinen Abstand nach oben durch Text gibt
    url_input = c1.text_input("Link:", placeholder="URL einfügen...", label_visibility="collapsed")
    
    if c2.button("🚀 Scan", type="primary", use_container_width=True):
        with st.status("Analysiere..."):
            raw = fetch_listings_from_url(url_input)
            st.session_state.raw_data = raw
            if raw: st.session_state.results = run_triage_analyst(raw, selected_model)
            else: st.error("Nichts gefunden.")

    if st.session_state.get('results'):
        df = pd.DataFrame(st.session_state.results.get('tabelle', []))
        
        if not df.empty:
            url_map = {item['id']: item['url'] for item in st.session_state.raw_data}
            df['link_url'] = df['original_id'].map(url_map)
            df = df.sort_values(by='score', ascending=False)
            
            st.dataframe(
                df[['link_url', 'score', 'kaufpreis', 'objektname', 'begruendung']],
                column_config={
                    "link_url": st.column_config.LinkColumn("Inserat", display_text="🔗 Öffnen", width="small"),
                    "score": st.column_config.NumberColumn("Score", format="%d / 10"),
                    "kaufpreis": st.column_config.NumberColumn("Kaufpreis", format="%.0f €"),
                    "begruendung": st.column_config.TextColumn("KI-Begründung", width="large")
                },
                use_container_width=True, hide_index=True
            )

            st.divider()
            
            obj_options = {f"[{r['score']}/10] {r['objektname']}": r['original_id'] for _, r in df.iterrows()}
            sel_name = st.selectbox("Objekt wählen:", list(obj_options.keys()))
            target = next((x for x in st.session_state.raw_data if x['id'] == obj_options[sel_name]), None)
            
            if target:
                c_a, c_b = st.columns(2, gap="medium")
                with c_a:
                    if st.button("✨ Schneller Deep-Dive (Vorprüfung)", use_container_width=True):
                        with st.spinner("Analysiere..."):
                            res = run_deep_dive_analyst(target, user_profile, selected_model)
                            st.markdown(res)
                with c_b:
                    if st.button("⭐ In Watchlist speichern", type="primary", use_container_width=True):
                        ok, msg = save_to_watchlist(st.session_state.user_email, target)
                        if ok: st.success(msg)
                        else: st.warning(msg)

# --- PAGE 2: WATCHLIST ---
elif page == "📂 Meine Watchlist":
    st.title("📂 Meine digitale Akte")
    saved_items = get_user_watchlist(st.session_state.user_email)
    
    if not saved_items:
        st.info("Watchlist ist noch leer. Speichere erst Objekte aus der Suche.")
    else:
        col_list, col_detail = st.columns([1, 2])
        with col_list:
            selected_db_id = st.radio("Gespeichert:", [i['db_id'] for i in saved_items], format_func=lambda x: next((i['title'] for i in saved_items if i['db_id'] == x), "?"))
        
        current_item = next((i for i in saved_items if i['db_id'] == selected_db_id), None)
        
        with col_detail:
            if current_item:
                listing_data = current_item['data']
                st.subheader(f"🏠 {current_item['title']}")
                st.write(f"**Preis:** {current_item['price']:,.0f} € | **Datum:** {current_item['date']}")
                st.link_button("Zum Original-Inserat", current_item['url'])
                
                has_docs = "--- DOKUMENT:" in listing_data.get('text', '')
                
                st.divider()
                st.markdown("### 📄 Dokumenten-Scanner")
                
                if has_docs:
                    st.success("✅ Dokumenten-Daten sind gespeichert!")
                
                st.info("Lade hier Exposés, Hausgeldabrechnungen oder Protokolle hoch:")
                uploaded_files = st.file_uploader("PDFs hier reinziehen", type=["pdf", "txt"], accept_multiple_files=True)
                
                if uploaded_files:
                    if st.button("💾 Einlesen & Speichern", use_container_width=True):
                        all_text = ""
                        my_bar = st.progress(0)
                        for i, f in enumerate(uploaded_files):
                            try:
                                if f.type == "application/pdf":
                                    reader = PdfReader(f)
                                    text = ""
                                    for p in reader.pages: text += p.extract_text()
                                    all_text += f"\n\n--- DOKUMENT: {f.name} ---\n{text}"
                                else:
                                    text = f.read().decode("utf-8")
                                    all_text += f"\n\n--- DOKUMENT: {f.name} ---\n{text}"
                            except Exception as e: st.error(f"Fehler {f.name}: {e}")
                            my_bar.progress((i+1)/len(uploaded_files))
                        
                        my_bar.empty()
                        listing_data['text'] = listing_data['text'] + all_text
                        update_watchlist_entry(current_item['db_id'], listing_data)
                        st.success("Gespeichert! Seite lädt neu...")
                        time.sleep(1.5)
                        st.rerun()

                st.divider()
                
                c_chk, c_bank = st.columns(2, gap="medium")
                
                with c_chk:
                    if st.button("🔄 Aktenlage prüfen", use_container_width=True):
                        with st.spinner("Prüfe alle Dokumente..."):
                            res = run_deep_dive_analyst(listing_data, user_profile, selected_model)
                            st.markdown("### 🕵️‍♂️ Ergebnis der Prüfung")
                            st.markdown(res)
                
                with c_bank:
                    if st.button("🏦 Bank-Exposé erstellen", type="primary", use_container_width=True):
                        with st.spinner("Verfasse Bank-Anschreiben & Generiere PDF..."):
                            expose_text = generate_bank_expose(listing_data, user_profile, selected_model)
                            pdf_bytes = create_pdf(expose_text, st.session_state.user_email)
                            st.success("PDF erstellt!")
                            st.markdown("### 📄 Entwurf für die Bank")
                            st.text_area("Vorschau (Inhalt):", expose_text, height=200)
                            st.download_button("⬇️ Bank_Expose.pdf herunterladen", pdf_bytes, f"Expose_{current_item['db_id']}.pdf", "application/pdf", type="primary", use_container_width=True)

                st.divider()
                if st.button("🗑️ Aus Watchlist löschen", type="secondary"):
                    delete_from_watchlist(current_item['db_id']); st.rerun()
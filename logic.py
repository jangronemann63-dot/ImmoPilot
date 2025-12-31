import google.generativeai as genai
from apify_client import ApifyClient
import json
import streamlit as st
import hashlib
import re

# KEYS
GOOGLE_KEY = st.secrets["GOOGLE_KEY"]
APIFY_TOKEN = st.secrets["APIFY_TOKEN"]

genai.configure(api_key=GOOGLE_KEY)

GRUNDERWERBSTEUER = {
    "Bayern": 3.5, "Sachsen": 5.5, "Baden-Württemberg": 5.0, "Bremen": 5.0,
    "Niedersachsen": 5.0, "Rheinland-Pfalz": 5.0, "Sachsen-Anhalt": 5.0,
    "Hamburg": 5.5, "Berlin": 6.0, "Hessen": 6.0, "Mecklenburg-Vorpommern": 6.0,
    "Brandenburg": 6.5, "Nordrhein-Westfalen": 6.5, "Saarland": 6.5,
    "Schleswig-Holstein": 6.5, "Thüringen": 5.0
}

def _parse_price(price_str):
    if not price_str: return 0
    try:
        clean = str(price_str).replace(".", "").replace("€", "").replace("VB", "").strip()
        return float(clean.replace(",", "."))
    except: return 0

def _clean_json_string(json_str):
    if not json_str: return "{}"
    pattern = r"```json\s*(.*?)\s*```"
    match = re.search(pattern, json_str, re.DOTALL)
    if match: return match.group(1)
    return json_str.replace("```json", "").replace("```", "").strip()

def _extract_value_from_text(text, pattern_type):
    text = text.lower()
    if pattern_type == "rent":
        match = re.search(r'(?:kaltmiete|km|miete|me)\s*[:=]?\s*(\d+[.,]?\d*)', text)
        if match: return float(match.group(1).replace(".", "").replace(",", "."))
    if pattern_type == "sqm":
        match = re.search(r'(\d+[.,]?\d*)\s*(?:qm|m²|m2)', text)
        if match: return float(match.group(1).replace(".", "").replace(",", "."))
    return 0

def get_available_models():
    try:
        return [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    except: return ["gemini-pro", "gemini-1.5-flash"]

def fetch_listings_from_url(url):
    client = ApifyClient(APIFY_TOKEN)
    try:
        call = client.actor("webdatalabs/ebay-kleinanzeigen-scraper").call(run_input={"searchUrl": url, "maxItems": 20})
        items = client.dataset(call["defaultDatasetId"]).list_items().items
        clean = []
        for item in items:
            title = item.get("title") or "Unbekannt"
            price = item.get("price") or 0
            link = item.get("url") or item.get("detailUrl")
            desc = item.get("description", "")
            loc = item.get("location", "")
            
            raw_id = str(item.get("adId", ""))
            if not raw_id or raw_id == "0": raw_id = hashlib.md5(link.encode()).hexdigest() if link else "unknown"

            details = ""
            for k in ["livingSpace", "rooms", "condition", "constructionYear", "energyLabel", "hausgeld"]:
                if item.get(k): details += f"{k}: {item.get(k)}\n"
            
            full_text = f"TITEL: {title}\nPREIS: {price}\nORT: {loc}\nDETAILS:\n{details}\nDESC: {desc[:1500]}\nLINK: {link}"
            clean.append({"id": raw_id, "objektname": title, "preis": _parse_price(price), "text": full_text, "url": link})
        return clean
    except Exception as e:
        st.error(f"Apify Fehler: {e}")
        return []

# --- TRIAGE (OPTIMIERT FÜR INVESTOREN) ---
def run_triage_analyst(listings, model_name):
    if not listings: return {"error": "Keine Daten."}
    
    # Wir übergeben nur relevante Daten, um Tokens zu sparen
    # Aber wir fügen "preis_pro_qm" hinzu, falls wir qm haben, damit die KI rechnen kann
    listings_json = json.dumps([{k: v for k, v in l.items() if k != 'text'} for l in listings], ensure_ascii=False)
    
    model = genai.GenerativeModel(model_name, generation_config={"response_mime_type": "application/json"})
    
    prompt = f"""
    Rolle: Gnadenloser Immobilien-Investment-Screener.
    ZIEL: Finde Objekte für KAPITALANLEGER (Cashflow & Rendite), NICHT für Selbstnutzer.
    
    INPUT DATEN:
    {listings_json}
    
    BEWERTUNGS-LOGIK (Score 1-10):
    
    GEBIET: Fokus auf Zahlen und Potenzial.
    
    ABZÜGE (Score runter):
    - "Luxus", "Traumhaus", "Liebhaberobjekt" -> Meist zu teuer für Rendite (Max Score 5).
    - Sehr hoher Preis (> 500.000 €) bei kleiner Wohnung.
    - Neubau / Erstbezug (oft zu teuer für Cashflow).
    - Unklare Preise (0 € oder 1 €).
    
    BONUS (Score hoch):
    - "Vermietet", "Kapitalanlage", "Rendite".
    - "Renovierungsbedürftig", "Handwerker" (Chance auf Wertsteigerung).
    - Günstiger Preis im Verhältnis zur Größe (Schnäppchen-Verdacht).
    - "Zwangsversteigerung", "Notverkauf".
    - Mehrfamilienhäuser oder Pakete.
    
    AUFGABE:
    Erstelle eine JSON Tabelle.
    OUTPUT SCHEMA: {{ "tabelle": [ {{ "original_id": "ID", "objektname": "Titel", "kaufpreis": 123, "score": 1-10, "status": "HOT/WATCHLIST/TRASH", "begruendung": "Kurz: Warum gut/schlecht für INVESTOREN?" }} ] }}
    """
    
    try:
        response = model.generate_content(prompt)
        return json.loads(_clean_json_string(response.text))
    except Exception as e:
        return {"error": str(e)}

def run_deep_dive_analyst(listing, profile, model_name):
    kp = listing['preis']
    nk = kp * ((GRUNDERWERBSTEUER.get(profile['bundesland'], 6.5) + 2.0 + profile['makler_prozent'])/100)
    invest = kp + nk + profile['sanierung']
    
    data = f"""
    Preis: {kp}, NK: {nk}, Gesamt: {invest}, Zins: {profile['zins']}%, 
    User-EK: {profile['ek']}, User-Netto: {profile['net_income']}, Steuer: {profile['tax']}%
    Objekt-Text: {listing['text']}
    """
    prompt = f"Rolle: Immo-Investment-Profi. Analysiere Cashflow, Steuer, Risiko für dieses Objekt & Profil. Sei kritisch.\nDaten: {data}"
    try: return genai.GenerativeModel(model_name).generate_content(prompt).text
    except Exception as e: return str(e)

def generate_bank_expose(listing, profile, model_name):
    kp = listing['preis']
    nk_perc = GRUNDERWERBSTEUER.get(profile['bundesland'], 6.5) + 2.0 + profile['makler_prozent']
    nk = kp * (nk_perc/100)
    invest = kp + nk + profile['sanierung']
    
    ek_soll = nk + profile['sanierung']
    kredit = kp if profile['ek'] < ek_soll + (kp*0.2) else kp * 0.8
    
    data = f"""
    Kaufpreis: {kp}, Nebenkosten: {nk} ({nk_perc}%), Sanierung: {profile['sanierung']}
    Gesamt-Invest: {invest}. Finanzierungsbedarf: {kredit}
    Objekt: {listing['text']}
    """
    
    prompt = f"""
    Erstelle ein professionelles Bank-Exposé (Investitions-Memorandum) für den Kreditentscheider.
    Struktur: Executive Summary, Objekt/Lage, Investitionsrechnung, Kapitaldienstfähigkeit, Fazit.
    Tonalität: Bank-Deutsch, sehr seriös.
    Daten: {data}
    """
    try: return genai.GenerativeModel(model_name).generate_content(prompt).text
    except Exception as e: return str(e)

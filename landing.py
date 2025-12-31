def get_landing_page_html():
    return """
    <style>
        /* STREAMLIT HACKS FÜR VOLLBILD */
        .block-container {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
            max-width: 100% !important;
        }
        [data-testid="stHeader"] {
            display: none; /* Versteckt den Streamlit Header */
        }
        /* DEIN LANDING PAGE STYLE */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        .landing-body { 
            font-family: 'Inter', sans-serif; 
            background-color: #f8fafc; 
            color: #0f172a;
            margin: 0;
        }
        .gradient-text {
            background: linear-gradient(to right, #2563eb, #9333ea);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        /* Tailwind-ähnliche Utility Classes (vereinfacht für Streamlit) */
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .text-center { text-align: center; }
        .btn { 
            display: inline-block; 
            padding: 12px 24px; 
            border-radius: 8px; 
            text-decoration: none; 
            font-weight: 600; 
            margin: 10px;
        }
        .btn-primary { background-color: #2563eb; color: white !important; }
        .btn-secondary { background-color: white; color: #334155 !important; border: 1px solid #cbd5e1; }
        .hero-section { padding: 100px 20px; text-align: center; background: white; }
        .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; padding: 50px 20px; }
        .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
        .comparison-box { display: flex; gap: 20px; margin-top: 40px; justify-content: center; flex-wrap: wrap;}
        .comp-card { flex: 1; padding: 20px; border-radius: 10px; min-width: 300px; }
        .comp-bad { background: #1e293b; color: #94a3b8; border: 1px solid #334155; }
        .comp-good { background: rgba(30, 58, 138, 0.1); border: 2px solid #3b82f6; color: #1e3a8a; }
    </style>

    <div class="landing-body">
        <div class="hero-section">
            <div style="background: #eff6ff; color: #1d4ed8; padding: 5px 15px; border-radius: 20px; display: inline-block; margin-bottom: 20px; font-size: 0.9rem; font-weight: 600;">
                🚀 Neu: Der "Hunnentränke"-Detektor
            </div>
            <h1 style="font-size: 3.5rem; line-height: 1.2; margin-bottom: 20px; color: #0f172a;">
                Der Makler sagt "Traumhaus".<br>
                <span class="gradient-text">Die KI findet den Wasserschaden auf Seite 84.</span>
            </h1>
            <p style="font-size: 1.25rem; color: #64748b; max-width: 800px; margin: 0 auto 40px auto;">
                Lade Exposés und Protokolle hoch. ImmoPilot AI prüft hunderte Seiten in Sekunden, findet versteckte Risiken und erstellt dein Bank-Exposé.
            </p>
            <div>
                <div style="font-size: 0.9rem; color: #64748b; margin-top: 10px;">
                    👉 <b>Logge dich links in der Sidebar ein, um zu starten!</b>
                </div>
            </div>
        </div>

        <div style="background: #0f172a; color: white; padding: 80px 20px;">
            <div class="container">
                <h2 class="text-center" style="font-size: 2rem; margin-bottom: 10px;">Warum du ohne KI blind fliegst</h2>
                <p class="text-center" style="color: #94a3b8; margin-bottom: 40px;">Ein echtes Beispiel aus unserer Analyse ("Dortmund Hunnentränke"):</p>
                
                <div class="comparison-box">
                    <div class="comp-card comp-bad">
                        <h3 style="color: #ef4444; font-weight: bold; margin-bottom: 10px;">WAS DER MAKLER SAGT</h3>
                        <p style="font-size: 1.1rem; margin-bottom: 20px;">"Modernisiertes Dachgeschoss, Baujahr 1995"</p>
                        <hr style="border-color: #334155; margin-bottom: 20px;">
                        <p style="color: #ef4444; font-family: monospace;">>> Risiko: Falsche AfA & unerkannter Sanierungsstau.</p>
                    </div>
                    
                    <div class="comp-card comp-good">
                        <h3 style="color: #22c55e; font-weight: bold; margin-bottom: 10px;">WAS IMMOPILOT FINDET</h3>
                        <div style="margin-bottom: 15px;">
                            <strong>🔍 Widerspruch erkannt!</strong><br>
                            "Im Versicherungsschein (S. 69) steht <u>Baujahr 1960</u>. Das Inserat behauptet 1995."
                        </div>
                        <div>
                            <strong>⚠️ Versteckte Kosten</strong><br>
                            "WEG-Protokoll 2023: Beschluss über 'nur unabwendbare Instandsetzung' wegen Geldmangel."
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div style="padding: 80px 20px; background: #f8fafc;">
            <div class="container text-center">
                <h2 style="font-size: 2rem; color: #0f172a; margin-bottom: 40px;">Investiere in Sicherheit, nicht in Hoffnung</h2>
                <div class="feature-grid">
                    <div class="card">
                        <h3>Schnupper-Check</h3>
                        <div style="font-size: 2.5rem; font-weight: bold; color: #2563eb; margin: 10px 0;">19 €</div>
                        <p style="color: #64748b;">Für den ersten Check vor der Besichtigung.</p>
                    </div>
                    <div class="card" style="border: 2px solid #2563eb; transform: scale(1.05);">
                        <div style="background: #2563eb; color: white; display: inline-block; padding: 2px 10px; border-radius: 10px; font-size: 0.8rem; margin-bottom: 10px;">BELIEBT</div>
                        <h3>Der Investor</h3>
                        <div style="font-size: 2.5rem; font-weight: bold; color: #2563eb; margin: 10px 0;">49 €</div>
                        <p style="color: #64748b;">5 Deep-Dives inkl. Watchlist & Verlauf.</p>
                    </div>
                    <div class="card">
                        <h3>Profi</h3>
                        <div style="font-size: 2.5rem; font-weight: bold; color: #2563eb; margin: 10px 0;">149 €</div>
                        <p style="color: #64748b;">White-Label Exposés für Makler.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
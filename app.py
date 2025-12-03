import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time

st.set_page_config(page_title="Data Quality Dashboard", layout="wide")

st.markdown("""
    <style>
    .metric-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

class AnalyseurQualite:
    
    def __init__(self, df):
        self.df = df
        self.resultats = {}
        self.checks_ok = 0
        self.checks_total = 15
        self.timestamp = datetime.now()
    
    def check_valeurs_manquantes(self):
        missing_pct = (self.df.isna().sum() / len(self.df) * 100).to_dict()
        total = self.df.isna().sum().sum()
        ok = total == 0
        
        self.resultats['valeurs_manquantes'] = {
            'passed': ok,
            'detail': f"Total missing: {total}",
            'by_column': missing_pct,
            'severity': 'CRITICAL' if total > len(self.df) * 0.1 else 'WARNING' if total > 0 else 'OK'
        }
        if ok:
            self.checks_ok += 1
    
    def check_doublons(self):
        if 'TradeID' in self.df.columns:
            dupes = self.df['TradeID'].duplicated().sum()
            ok = dupes == 0
        else:
            dupes = self.df.duplicated().sum()
            ok = dupes == 0
        
        self.resultats['doublons'] = {
            'passed': ok,
            'count': dupes,
            'percentage': dupes / len(self.df) * 100 if len(self.df) > 0 else 0,
            'severity': 'CRITICAL' if dupes > 0 else 'OK'
        }
        if ok:
            self.checks_ok += 1
    
    def check_types(self):
        problemes = {}
        colonnes_date = ['Date', 'SettlementDate', 'CreatedAt']
        
        for col in colonnes_date:
            if col in self.df.columns:
                try:
                    pd.to_datetime(self.df[col])
                except:
                    problemes[col] = 'Format date invalide'
        
        ok = len(problemes) == 0
        self.resultats['types'] = {
            'passed': ok,
            'issues': problemes,
            'severity': 'WARNING' if problemes else 'OK'
        }
        if ok:
            self.checks_ok += 1
    
    def check_outliers(self):
        nb_outliers = 0
        details = {}
        
        cols_num = self.df.select_dtypes(include=[np.number]).columns
        for col in cols_num:
            if self.df[col].notna().sum() > 0:
                q1 = self.df[col].quantile(0.25)
                q3 = self.df[col].quantile(0.75)
                iqr = q3 - q1
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                
                outliers = ((self.df[col] < lower) | (self.df[col] > upper)).sum()
                if outliers > 0:
                    nb_outliers += outliers
                    details[col] = outliers
        
        ok = nb_outliers == 0
        self.resultats['outliers'] = {
            'passed': ok,
            'total': nb_outliers,
            'detail': details,
            'severity': 'WARNING' if nb_outliers > len(self.df) * 0.05 else 'INFO' if nb_outliers > 0 else 'OK'
        }
        if ok:
            self.checks_ok += 1
    
    def check_ranges(self):
        problemes = {}
        
        if 'Quantity' in self.df.columns:
            invalides = (self.df['Quantity'] < 0).sum()
            if invalides > 0:
                problemes['Quantity'] = f"{invalides} valeurs négatives"
        
        if 'Price' in self.df.columns:
            invalides = (self.df['Price'] < 0).sum()
            if invalides > 0:
                problemes['Price'] = f"{invalides} valeurs négatives"
        
        if 'Commission' in self.df.columns:
            invalides = ((self.df['Commission'] < 0) | (self.df['Commission'] > 1)).sum()
            if invalides > 0:
                problemes['Commission'] = f"{invalides} hors range"
        
        ok = len(problemes) == 0
        self.resultats['ranges'] = {
            'passed': ok,
            'issues': problemes,
            'severity': 'CRITICAL' if problemes else 'OK'
        }
        if ok:
            self.checks_ok += 1
    
    def check_dates(self):
        problemes = {}
        
        if 'Date' in self.df.columns and 'SettlementDate' in self.df.columns:
            try:
                dates = pd.to_datetime(self.df['Date'])
                settlement = pd.to_datetime(self.df['SettlementDate'])
                
                invalides = (settlement < dates).sum()
                if invalides > 0:
                    problemes['settlement_avant_trade'] = invalides
            except:
                problemes['erreur_parsing'] = True
        
        ok = len(problemes) == 0
        self.resultats['dates'] = {
            'passed': ok,
            'issues': problemes,
            'severity': 'CRITICAL' if problemes else 'OK'
        }
        if ok:
            self.checks_ok += 1
    
    def check_categoriques(self):
        problemes = {}
        
        if 'Status' in self.df.columns:
            valides = ['EXECUTED', 'PENDING', 'CANCELLED', 'SETTLED', 'CONFIRMED']
            invalides = (~self.df['Status'].isin(valides)).sum()
            if invalides > 0:
                problemes['Status'] = f"{invalides} valeurs invalides"
        
        if 'TradeType' in self.df.columns:
            valides = ['SPOT', 'FORWARD', 'SWAP', 'OPTION', 'NDF']
            invalides = (~self.df['TradeType'].isin(valides)).sum()
            if invalides > 0:
                problemes['TradeType'] = f"{invalides} valeurs invalides"
        
        ok = len(problemes) == 0
        self.resultats['categoriques'] = {
            'passed': ok,
            'issues': problemes,
            'severity': 'WARNING' if problemes else 'OK'
        }
        if ok:
            self.checks_ok += 1
    
    def check_integrite(self):
        problemes = {}
        
        if 'Counterparty' in self.df.columns:
            manquants = self.df['Counterparty'].isna().sum()
            if manquants > 0:
                problemes['counterparty_manquant'] = manquants
        
        if 'Instrument' in self.df.columns:
            manquants = self.df['Instrument'].isna().sum()
            if manquants > 0:
                problemes['instrument_manquant'] = manquants
        
        ok = len(problemes) == 0
        self.resultats['integrite'] = {
            'passed': ok,
            'issues': problemes,
            'severity': 'CRITICAL' if problemes else 'OK'
        }
        if ok:
            self.checks_ok += 1
    
    def check_calculs(self):
        problemes = {}
        
        if 'Value' in self.df.columns and 'Quantity' in self.df.columns and 'Price' in self.df.columns:
            attendu = self.df['Quantity'] * self.df['Price']
            ecart = (abs(self.df['Value'] - attendu) / (abs(attendu) + 1) > 0.01).sum()
            if ecart > 0:
                problemes['calcul_value'] = f"{ecart} lignes avec écart > 1%"
        
        ok = len(problemes) == 0
        self.resultats['calculs'] = {
            'passed': ok,
            'issues': problemes,
            'severity': 'WARNING' if problemes else 'OK'
        }
        if ok:
            self.checks_ok += 1
    
    def check_strings(self):
        problemes = {}
        
        cols_text = self.df.select_dtypes(include=['object']).columns
        for col in cols_text:
            leading = self.df[col].astype(str).str.startswith(' ').sum()
            trailing = self.df[col].astype(str).str.endswith(' ').sum()
            
            if leading > 0 or trailing > 0:
                problemes[col] = f"{leading + trailing} espaces"
        
        ok = len(problemes) == 0
        self.resultats['strings'] = {
            'passed': ok,
            'issues': problemes,
            'severity': 'INFO' if problemes else 'OK'
        }
        if ok:
            self.checks_ok += 1
    
    def check_logique_metier(self):
        problemes = {}
        
        if 'Quantity' in self.df.columns:
            zeros = (self.df['Quantity'] == 0).sum()
            if zeros > 0:
                problemes['quantity_zero'] = zeros
        
        if 'Price' in self.df.columns:
            zeros = (self.df['Price'] == 0).sum()
            if zeros > 0:
                problemes['price_zero'] = zeros
        
        ok = len(problemes) == 0
        self.resultats['logique_metier'] = {
            'passed': ok,
            'issues': problemes,
            'severity': 'WARNING' if problemes else 'OK'
        }
        if ok:
            self.checks_ok += 1
    
    def check_completude(self):
        cols_requises = ['TradeID', 'Date', 'Instrument', 'Quantity', 'Price', 'Status']
        manquantes = [col for col in cols_requises if col not in self.df.columns]
        
        ok = len(manquantes) == 0
        self.resultats['completude'] = {
            'passed': ok,
            'colonnes_manquantes': manquantes,
            'total_colonnes': len(self.df.columns),
            'severity': 'CRITICAL' if manquantes else 'OK'
        }
        if ok:
            self.checks_ok += 1
    
    def check_timestamps(self):
        problemes = {}
        
        if 'EntryTime' in self.df.columns:
            try:
                pd.to_datetime(self.df['EntryTime'], format='%H:%M:%S')
            except:
                problemes['format_time_invalide'] = True
        
        ok = len(problemes) == 0
        self.resultats['timestamps'] = {
            'passed': ok,
            'issues': problemes,
            'severity': 'WARNING' if problemes else 'OK'
        }
        if ok:
            self.checks_ok += 1
    
    def check_distribution(self):
        problemes = {}
        
        cols_num = self.df.select_dtypes(include=[np.number]).columns
        for col in cols_num:
            if self.df[col].notna().sum() > 0:
                skew = self.df[col].skew()
                if abs(skew) > 3:
                    problemes[col] = f"Skewness élevé: {skew:.2f}"
        
        ok = len(problemes) == 0
        self.resultats['distribution'] = {
            'passed': ok,
            'issues': problemes,
            'severity': 'INFO' if problemes else 'OK'
        }
        if ok:
            self.checks_ok += 1
    
    def check_fraicheur(self):
        problemes = {}
        
        if 'Date' in self.df.columns:
            try:
                date_max = pd.to_datetime(self.df['Date']).max()
                jours = (datetime.now() - date_max).days
                if jours > 365:
                    problemes['age_donnees'] = f"Data age: {jours} jours"
            except:
                pass
        
        ok = len(problemes) == 0
        self.resultats['fraicheur'] = {
            'passed': ok,
            'issues': problemes,
            'severity': 'INFO' if problemes else 'OK'
        }
        if ok:
            self.checks_ok += 1
    
    def analyser_tout(self):
        self.check_valeurs_manquantes()
        self.check_doublons()
        self.check_types()
        self.check_outliers()
        self.check_ranges()
        self.check_dates()
        self.check_categoriques()
        self.check_integrite()
        self.check_calculs()
        self.check_strings()
        self.check_logique_metier()
        self.check_completude()
        self.check_timestamps()
        self.check_distribution()
        self.check_fraicheur()
    
    def score_qualite(self):
        score = 100
        
        for nom, res in self.resultats.items():
            sev = res.get('severity', 'OK')
            if sev == 'CRITICAL':
                score -= 15
            elif sev == 'WARNING':
                score -= 5
            elif sev == 'INFO':
                score -= 1
        
        return max(0, score)
    
    def resume(self):
        return {
            'total_checks': self.checks_total,
            'checks_ok': self.checks_ok,
            'score': self.score_qualite(),
            'nb_lignes': len(self.df),
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }

st.title("Data Quality Dashboard")
st.markdown("Analyse de qualité des données financières")

with st.sidebar:
    st.header("Settings")
    mode = st.radio("Mode:", ["Upload CSV/Excel", "Use Sample Data"])

debut = time.time()

if mode == "Upload CSV/Excel":
    fichier = st.file_uploader("Upload ton fichier", type=["csv", "xlsx", "xls"])
    
    if fichier is not None:
        try:
            if fichier.name.endswith('.csv'):
                df = pd.read_csv(fichier)
            else:
                df = pd.read_excel(fichier)
            
            st.success(f"Fichier chargé: {fichier.name} ({len(df)} lignes, {len(df.columns)} colonnes)")
        except Exception as e:
            st.error(f"Erreur: {e}")
            st.stop()
    else:
        st.info("Upload un CSV ou Excel")
        st.stop()
else:
    try:
        df = pd.read_csv('financial_trades_sample.csv')
        st.success(f"Sample  {len(df)} lignes, {len(df.columns)} colonnes")
    except:
        st.warning("Sample data introuvable. Lance generate_dataset.py d'abord.")
        st.stop()

analyseur = AnalyseurQualite(df)
analyseur.analyser_tout()
temps_exec = time.time() - debut

col1, col2, col3, col4 = st.columns(4)

resume = analyseur.resume()
score = resume['score']

if score >= 90:
    status = "Excellent"
    color = "quality-score-high"
elif score >= 70:
    status = "Good"
    color = "quality-score-medium"
else:
    status = "Poor"
    color = "quality-score-low"

with col1:
    st.metric("Quality Score", f"{score}%")

with col2:
    st.metric("Lignes", f"{resume['nb_lignes']:,}")

with col3:
    st.metric("Checks OK", f"{resume['checks_ok']}/{resume['total_checks']}")

with col4:
    st.metric("Temps", f"{temps_exec:.2f}s")

st.markdown(f"**Status:** {status}")

st.markdown("---")
st.header("Analyse détaillée")

tab1, tab2, tab3 = st.tabs(["Résultats", "Preview Data", "Visualisations"])

with tab1:
    for nom, res in analyseur.resultats.items():
        nom_affiche = nom.replace('_', ' ').title()
        icone = "✅" if res['passed'] else "❌"
        sev = res.get('severity', 'OK')
        
        with st.expander(f"{icone} {nom_affiche} [{sev}]", expanded=False):
            if res['passed']:
                st.success("PASSED")
            else:
                st.error("FAILED")
            
            for k, v in res.items():
                if k != 'passed':
                    st.write(f"**{k}:** {v}")

with tab2:
    st.subheader("Dataset Preview")
    st.dataframe(df.head(20), use_container_width=True)
    
    st.subheader("Infos")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Lignes:** {len(df)}")
        st.write(f"**Colonnes:** {len(df.columns)}")
    with col2:
        st.write(f"**Mémoire:** {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

with tab3:
    col1, col2 = st.columns(2)
    
    with col1:
        statuts_checks = pd.Series([1 if r['passed'] else 0 for r in analyseur.resultats.values()],
                                   index=[k.replace('_', ' ').title() for k in analyseur.resultats.keys()])
        fig1 = px.bar(statuts_checks, 
                     labels={'index': 'Check', 'value': 'Status'},
                     color=statuts_checks.values,
                     color_continuous_scale=['#e74c3c', '#27ae60'],
                     title="Statut des Checks")
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        missing = (df.isna().sum() / len(df) * 100).sort_values(ascending=False)
        missing = missing[missing > 0]
        if len(missing) > 0:
            fig2 = px.bar(missing,
                         labels={'index': 'Colonne', 'value': 'Missing %'},
                         title="Valeurs Manquantes",
                         color=missing.values,
                         color_continuous_scale='Reds')
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Aucune valeur manquante")
    
    cols_num = df.select_dtypes(include=[np.number]).columns
    if len(cols_num) > 0:
        col_select = st.selectbox("Colonne pour distribution:", cols_num)
        fig3 = px.histogram(df, x=col_select, nbins=50, title=f"Distribution: {col_select}")
        st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")
st.header("Export")

if st.button("Générer Rapport HTML"):
    rapport = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Rapport Qualité Données</title>
        <style>
            body {{ font-family: Arial; margin: 20px; background: #f5f5f5; }}
            .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
            .summary {{ background: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 5px; }}
            .check {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #3498db; }}
            .passed {{ border-left-color: #27ae60; }}
            .failed {{ border-left-color: #e74c3c; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Rapport Qualité Données</h1>
            <p>Généré: {resume['timestamp']}</p>
        </div>
        
        <div class="summary">
            <h2>Résumé</h2>
            <p><strong>Score:</strong> {score}%</p>
            <p><strong>Lignes:</strong> {resume['nb_lignes']:,}</p>
            <p><strong>Checks OK:</strong> {resume['checks_ok']}/{resume['total_checks']}</p>
            <p><strong>Temps:</strong> {temps_exec:.2f}s</p>
        </div>
        
        <h2>Checks Détaillés</h2>
    """
    
    for nom, res in analyseur.resultats.items():
        nom_affiche = nom.replace('_', ' ').title()
        classe = 'passed' if res['passed'] else 'failed'
        sev = res.get('severity', 'OK')
        
        rapport += f"""
        <div class="check {classe}">
            <h3>{nom_affiche} [{sev}]</h3>
            <p><strong>Status:</strong> {'PASSED ✓' if res['passed'] else 'FAILED ✗'}</p>
            <ul>
        """
        
        for k, v in res.items():
            if k != 'passed':
                rapport += f"<li>{k}: {v}</li>"
        
        rapport += "</ul></div>"
    
    rapport += "</body></html>"
    
    st.download_button(
        label="Télécharger Rapport HTML",
        data=rapport,
        file_name=f"rapport_qualite_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
        mime="text/html"
    )

st.markdown("---")
st.caption("Data Quality Dashboard v1.0")

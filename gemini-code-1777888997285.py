import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Calcolo NTC 2018 - Vento e Neve", layout="wide")

class SoftwareNTC2018_Streamlit:
    def __init__(self):
        self.zone_neve = {
            "Zona I-Alpina": {"qsk_min": 1.50, "a": 1.39, "b": 728},
            "Zona I-Mediterranea": {"qsk_min": 1.50, "a": 1.35, "b": 602},
            "Zona II": {"qsk_min": 1.00, "a": 0.85, "b": 481},
            "Zona III": {"qsk_min": 0.60, "a": 0.51, "b": 481}
        }
        self.zone_vento = {
            1: {"vb0": 25, "a0": 1000, "ks": 0.40}, 2: {"vb0": 25, "a0": 750, "ks": 0.45},
            3: {"vb0": 27, "a0": 500, "ks": 0.37}, 4: {"vb0": 28, "a0": 500, "ks": 0.35},
            5: {"vb0": 28, "a0": 750, "ks": 0.42}, 6: {"vb0": 28, "a0": 500, "ks": 0.35},
            7: {"vb0": 27, "a0": 1000, "ks": 0.48}, 8: {"vb0": 28, "a0": 1250, "ks": 0.49},
            9: {"vb0": 31, "a0": 500, "ks": 0.31}
        }
        self.esposizione = {
            "I": {"kr": 0.17, "z0": 0.01, "zmin": 2}, "II": {"kr": 0.19, "z0": 0.05, "zmin": 4},
            "III": {"kr": 0.20, "z0": 0.10, "zmin": 5}, "IV": {"kr": 0.22, "z0": 0.30, "zmin": 8},
            "V": {"kr": 0.23, "z0": 0.70, "zmin": 12}
        }

    def calcola(self, d_comune, d_struttura):
        # NEVE
        zn = self.zone_neve[d_comune['zona_neve']]
        as_m = d_comune['altitudine']
        qsk = zn['qsk_min'] if as_m <= 200 else zn['a'] * (1 + (as_m/zn['b'])**2)
        qs = qsk * d_struttura['mu'] * d_struttura['ce_neve'] * d_struttura['ct_neve']
        
        # VENTO
        zv = self.zone_vento[d_comune['zona_vento']]
        ca = 1.0 if as_m <= zv['a0'] else 1 + zv['ks'] * (as_m/zv['a0'] - 1)
        vb = zv['vb0'] * ca
        qb = 0.5 * 1.25 * (vb**2) / 1000
        esp = self.esposizione[d_comune['cat_esp']]
        z = max(d_struttura['altezza'], esp['zmin'])
        ce_z = (esp['kr'] * np.log(z/esp['z0'])) * (7 + esp['kr'] * np.log(z/esp['z0']))
        p = qb * ce_z * d_struttura['cp'] * d_struttura['cd'] * d_struttura['ct_vento']
        
        return {"qsk": qsk, "qs": qs, "vb": vb, "qb": qb, "ce_z": ce_z, "p": p}

# --- INTERFACCIA STREAMLIT ---
st.title("📊 Calcolo Azioni NTC 2018")
st.markdown("Replica software del file *Calcolo azione vento e neve NTC 2018*")

ntc = SoftwareNTC2018_Streamlit()

# SIDEBAR PER INPUT
st.sidebar.header("📍 Dati Sito")
nome_comune = st.sidebar.text_input("Comune", "Milano")
altitudine = st.sidebar.number_input("Altitudine (m.s.l.m.)", 0, 3000, 120)
z_neve = st.sidebar.selectbox("Zona Neve", list(ntc.zone_neve.keys()))
z_vento = st.sidebar.selectbox("Zona Vento", list(ntc.zone_vento.keys()))
cat_esp = st.sidebar.selectbox("Categoria Esposizione", list(ntc.esposizione.keys()), index=2)

st.sidebar.header("🏗️ Parametri Struttura")
h_struttura = st.sidebar.number_input("Altezza Struttura (m)", 1.0, 100.0, 12.0)
cp = st.sidebar.slider("Coeff. Forma (cp)", -1.5, 1.5, 0.8)
mu = st.sidebar.slider("Coeff. Forma Neve (mu)", 0.0, 2.0, 0.8)

# CALCOLO
d_comune = {"altitudine": altitudine, "zona_neve": z_neve, "zona_vento": z_vento, "cat_esp": cat_esp}
d_struttura = {"altezza": h_struttura, "cp": cp, "cd": 1.0, "ct_vento": 1.0, "mu": mu, "ce_neve": 1.0, "ct_neve": 1.0}

res = ntc.calcola(d_comune, d_struttura)

# VISUALIZZAZIONE RISULTATI
col1, col2 = st.columns(2)
with col1:
    st.subheader("❄️ Azione Neve")
    st.metric("Neve al suolo (qsk)", f"{res['qsk']:.3f} kN/m²")
    st.metric("Neve di progetto (qs)", f"{res['qs']:.3f} kN/m²")

with col2:
    st.subheader("💨 Azione Vento")
    st.metric("Velocità rif. (vb)", f"{res['vb']:.2f} m/s")
    st.metric("Pressione progetto (p)", f"{res['p']:.3f} kN/m²")

# GRAFICI
st.divider()
st.subheader("📈 Profili Analitici (Replica Excel Chart 7 & 8)")

altezze = np.linspace(0.1, max(h_struttura + 10, 30), 100)
esp_params = ntc.esposizione[cat_esp]
ce_vett = []
p_vett = []

for h in altezze:
    z_eff = max(h, esp_params['zmin'])
    c = (esp_params['kr'] * np.log(z_eff/esp_params['z0'])) * (7 + esp_params['kr'] * np.log(z_eff/esp_params['z0']))
    ce_vett.append(c)
    p_vett.append(res['qb'] * c * cp)

fig, ax = plt.subplots(1, 2, figsize=(12, 5))
ax[0].plot(ce_vett, altezze, color='green')
ax[0].set_title("Coeff. Esposizione ce(z)")
ax[0].grid(True, ls=':')

ax[1].plot(p_vett, altezze, color='blue')
ax[1].set_title("Pressione Progetto p(z) [kN/m²]")
ax[1].grid(True, ls=':')

st.pyplot(fig)
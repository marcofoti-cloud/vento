import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="NTC 2018 Pro - Vento e Neve", layout="wide")

class SoftwareNTC2018_Full:
    def __init__(self):
        # Database Zone (Replica integrale Excel)
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

    def calcola_mu_neve(self, tipo_tetto, inclinazione):
        # NTC 2018 Cap. 3.4.3
        if tipo_tetto == "Piano o Monofalda":
            if inclinazione <= 30: return 0.8
            elif inclinazione < 60: return 0.8 * (60 - inclinazione) / 30
            else: return 0.0
        else: # Doppia falda
            if inclinazione <= 30: return 0.8 + 0.8 * (inclinazione/30) # Semplificato per picco
            else: return 0.8

# --- INTERFACCIA ---
st.title("🏛️ Analisi Strutturale NTC 2018")
ntc = SoftwareNTC2018_Full()

# SIDEBAR: DATI GEOGRAFICI
st.sidebar.header("📍 Localizzazione")
altitudine = st.sidebar.number_input("Altitudine [m]", 0, 3000, 120)
z_neve = st.sidebar.selectbox("Zona Neve", list(ntc.zone_neve.keys()))
z_vento = st.sidebar.selectbox("Zona Vento", list(ntc.zone_vento.keys()), index=2)
cat_esp = st.sidebar.selectbox("Categoria Esposizione", list(ntc.esposizione.keys()), index=2)

# MAIN: FORMA EDIFICIO
st.header("📐 Geometria e Forma")
col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    altezza = st.number_input("Altezza edificio (z) [m]", 1.0, 100.0, 10.0)
    inclinazione = st.slider("Inclinazione falda [°]", 0, 90, 0)

with col_f2:
    tipo_tetto = st.selectbox("Tipologia Tetto", ["Piano o Monofalda", "Doppia Falda"])
    superficie_esposta = st.selectbox("Elemento per Vento", ["Parete Sopravento", "Parete Sottovento", "Copertura"])

with col_f3:
    # Impostazione automatica Cp in base alla scelta
    if superficie_esposta == "Parete Sopravento": cp_default = 0.8
    elif superficie_esposta == "Parete Sottovento": cp_default = -0.5
    else: cp_default = -0.7 # Copertura (depressione media)
    
    cp = st.number_input("Coeff. di forma (Cp)", -2.0, 2.0, cp_default)
    cd = st.number_input("Coeff. dinamico (Cd)", 0.0, 2.0, 1.0)

# LOGICA DI CALCOLO
# --- Neve ---
zn = ntc.zone_neve[z_neve]
qsk = zn['qsk_min'] if altitudine <= 200 else zn['a'] * (1 + (altitudine/zn['b'])**2)
mu = ntc.calcola_mu_neve(tipo_tetto, inclinazione)
qs = qsk * mu # Ipotesi Ce=1, Ct=1 come da Excel standard

# --- Vento ---
zv = ntc.zone_vento[z_vento]
ca = 1.0 if altitudine <= zv['a0'] else 1 + zv['ks'] * (altitudine/zv['a0'] - 1)
vb = zv['vb0'] * ca
qb = 0.5 * 1.25 * (vb**2) / 1000
esp = ntc.esposizione[cat_esp]
z_eff = max(altezza, esp['zmin'])
ce = (esp['kr'] * np.log(z_eff/esp['z0'])) * (7 + esp['kr'] * np.log(z_eff/esp['z0']))
p_progetto = qb * ce * cp * cd

# DISPLAY RISULTATI
st.divider()
c1, c2, c3 = st.columns(3)
c1.metric("Neve al suolo $q_{sk}$", f"{qsk:.2f} kN/m²")
c1.metric("Neve tetto $q_{s}$", f"{qs:.2f} kN/m²")

c2.metric("Velocità rif. $v_b$", f"{vb:.1f} m/s")
c2.metric("Pressione rif. $q_b$", f"{qb:.3f} kN/m²")

c3.metric("Coeff. Esposizione $c_e$", f"{ce:.3f}")
c3.metric("Pressione Progetto $p_d$", f"{p_progetto:.3f} kN/m²", delta_color="inverse")

# GRAFICI REPLICATI
st.subheader("📊 Analisi dell'Azione del Vento (Profili Altezza)")
h_range = np.linspace(0.1, max(altezza + 10, 20), 100)
ce_v = []
pz_v = []

for h in h_range:
    ze = max(h, esp['zmin'])
    c = (esp['kr'] * np.log(ze/esp['z0'])) * (7 + esp['kr'] * np.log(ze/esp['z0']))
    ce_v.append(c)
    pz_v.append(qb * c * cp * cd)

fig, ax = plt.subplots(1, 2, figsize=(12, 4))
ax[0].plot(ce_v, h_range, color='darkgreen')
ax[0].set_title("Evoluzione $c_e(z)$")
ax[0].set_ylabel("Altezza [m]")
ax[0].grid(True, ls=':')

ax[1].plot(pz_v, h_range, color='darkred')
ax[1].set_title("Pressione di Progetto $p(z)$ [kN/m²]")
ax[1].grid(True, ls=':')
st.pyplot(fig)
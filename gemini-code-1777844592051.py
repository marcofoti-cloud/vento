import streamlit as st
import math
import numpy as np
import matplotlib.pyplot as plt

class NTC2018VentoFull:
    def __init__(self):
        self.rho = 1.25
        self.nu = 1.5e-5

    def calcola_vb(self, zona, altitudine):
        mappa = {
            1: [25, 1000], 2: [25, 750], 3: [27, 500],
            4: [28, 500], 5: [28, 750], 6: [28, 500],
            7: [27, 1000], 8: [28, 1250], 9: [31, 1500]
        }
        vb0, a0 = mappa.get(zona, [25, 500])
        vb = vb0 if altitudine <= a0 else vb0 * (1 + 0.00001 * (altitudine - a0))
        return vb, vb0, a0

    def get_ce(self, z, kr, z0, zmin):
        ze = max(z, zmin)
        return (kr**2) * 1.0 * math.log(ze/z0) * (7 + math.log(ze/z0))

def genera_testo_relazione(d):
    return f"""RELAZIONE TECNICA DI CALCOLO: AZIONE DEL VENTO (NTC 2018)
-------------------------------------------------------

1. PARAMETRI DI RIFERIMENTO
- Vita Nominale (Vn): {d['vn']} anni
- Classe d'Uso: {d['classe_uso']} (Cu = {d['cu']})
- Periodo di Riferimento (Vr): {d['vr']} anni

2. LOCALIZZAZIONE SITO
- Zona di vento: {d['zona_v']}
- Altitudine: {d['altitudine']} m s.l.m.
- vb0: {d['vb0']} m/s | a0: {d['a0']} m
- Velocità di progetto (vb): {d['vb']:.2f} m/s

3. ESPOSIZIONE E TERRENO
- Classe rugosità: {d['classe_rug']}
- Distanza costa: {d['dist_mare']} km
- Categoria Esposizione: {d['cat']}
- Parametri: kr={d['kr']}, z0={d['z0']}m, zmin={d['zmin']}m
- Altezza edificio (z): {d['h_struttura']} m
- Coeff. Esposizione ce(z): {d['ce']:.4f}

4. GEOMETRIA E COEFFICIENTI
- Tipologia: {d['tipo_struttura']}
- Coeff. forma (cp/cf): {d['cp']}
{f"- Diametro: {d['diam']} m" if d['diam'] else ""}
{f"- Ostruzione (phi): {d['phi']}" if d['phi'] else ""}

5. RISULTATI FINALI
- Pressione cinetica (qb): {d['qb']:.4f} kN/m²
- Pressione di progetto (pe): {d['pe']:.4f} kN/m²

Il calcolo è stato eseguito secondo le Norme Tecniche per le Costruzioni 2018."""

# --- INTERFACCIA ---
st.set_page_config(page_title="NTC 2018 Full + Relazione", layout="wide")
st.title("🌪️ Vento NTC 2018: Calcolo e Relazione")

engine = NTC2018VentoFull()

# SIDEBAR
st.sidebar.header("1. Parametri Generali")
vn = st.sidebar.number_input("Vita Nominale Vn", 50, 200, 50)
classe_uso = st.sidebar.selectbox("Classe d'Uso", [1, 2, 3, 4], index=1)
cu_map = {1: 0.7, 2: 1.0, 3: 1.5, 4: 2.0}
vr = vn * cu_map[classe_uso]

st.sidebar.header("2. Sito")
zona_v = st.sidebar.selectbox("Zona Vento", range(1, 10), index=2)
altitudine = st.sidebar.number_input("Altitudine [m]", 0, 3000, 100)
dist_mare = st.sidebar.number_input("Distanza Mare [km]", 0.0, 100.0, 5.0)
classe_rug = st.sidebar.selectbox("Rugosità", ["A (Costa)", "B (Campagna)", "C (Industriale)", "D (Urbano)"])

# Logica Categoria
if dist_mare < 1: cat = "A"
else:
    cat = {"A (Costa)":"B", "B (Campagna)":"C", "C (Industriale)":"D", "D (Urbano)":"E"}[classe_rug]
kr, z0, zmin = {'A':[0.16, 0.01, 2], 'B':[0.19, 0.05, 4], 'C':[0.20, 0.10, 5], 'D':[0.22, 0.30, 8], 'E':[0.23, 0.70, 12]}[cat]

st.sidebar.header("3. Struttura")
tipo_s = st.sidebar.selectbox("Tipo", ["Rettangolare", "Cilindro", "Tettoia"])
h_s = st.sidebar.slider("Altezza z [m]", 2, 100, 15)

diam, phi = None, None
if tipo_s == "Rettangolare": cp = 0.8
elif tipo_s == "Cilindro":
    diam = st.sidebar.number_input("Diametro [m]", 1.0, 50.0, 5.0)
    cp = 1.2 # Approssimazione per report
else:
    phi = st.sidebar.slider("Ostruzione phi", 0.0, 1.0, 0.5)
    cp = 1.2 + 0.3 * phi

# CALCOLO
vb, vb0, a0 = engine.calcola_vb(zona_v, altitudine)
qb = 0.5 * engine.rho * (vb**2) / 1000
ce = engine.get_ce(h_s, kr, z0, zmin)
pe = qb * ce * cp

# DISPLAY
res = st.columns(4)
res[0].metric("Vr", f"{int(vr)}y")
res[1].metric("vb", f"{vb:.2f}m/s")
res[2].metric("ce", f"{ce:.3f}")
res[3].metric("pe", f"{pe:.3f}kN/m²")

# RELAZIONE
st.divider()
st.subheader("📄 Relazione di Calcolo")
d_rep = {
    'vn':vn, 'classe_uso':classe_uso, 'cu':cu_map[classe_uso], 'vr':vr,
    'zona_v':zona_v, 'altitudine':altitudine, 'vb0':vb0, 'a0':a0, 'vb':vb,
    'classe_rug':classe_rug, 'dist_mare':dist_mare, 'cat':cat,
    'kr':kr, 'z0':z0, 'zmin':zmin, 'h_struttura':h_s, 'ce':ce,
    'tipo_struttura':tipo_s, 'cp':cp, 'qb':qb, 'pe':pe, 'diam':diam, 'phi':phi
}
txt_rep = genera_testo_relazione(d_rep)
st.text_area("Anteprima (Copia-Incolla)", txt_rep, height=250)
st.download_button("📥 Scarica Relazione .txt", txt_rep, "relazione_vento.txt")

# GRAFICO
z_vals = np.linspace(0, h_s + 10, 100)
p_vals = [qb * engine.get_ce(z, kr, z0, zmin) * cp for z in z_vals]
fig, ax = plt.subplots(figsize=(8,3))
ax.plot(p_vals, z_vals, color='navy', label='Pressione pe(z)')
ax.axhline(h_s, color='red', ls='--')
ax.set_xlabel("Pressione [kN/m²]")
ax.set_ylabel("Altezza [m]")
st.pyplot(fig)
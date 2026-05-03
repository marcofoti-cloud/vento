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

# --- INTERFACCIA STREAMLIT ---
st.set_page_config(page_title="NTC 2018 Vento Full", layout="wide")
st.title("🌪️ Analizzatore Vento NTC 2018 Completo")

engine = NTC2018VentoFull()

# --- SIDEBAR: VITA UTILE E IMPORTANZA ---
st.sidebar.header("1. Vita Utile e Importanza")
vn = st.sidebar.number_input("Vita Nominale Vn [anni]", value=50, step=10)
classe_uso = st.sidebar.selectbox("Classe d'Uso", options=[1, 2, 3, 4], index=1)
cu_map = {1: 0.7, 2: 1.0, 3: 1.5, 4: 2.0}
vr = vn * cu_map[classe_uso]
st.sidebar.info(f"Periodo di Riferimento Vr: **{int(vr)} anni**")

# --- SIDEBAR: LOCALIZZAZIONE ---
st.sidebar.header("2. Localizzazione")
zona_v = st.sidebar.selectbox("Zona Vento", options=range(1, 10), index=2)
altitudine = st.sidebar.number_input("Altitudine [m s.l.m.]", value=100)

# --- SIDEBAR: RUGOSITÀ ---
st.sidebar.header("3. Rugosità e Costa")
classe_rug = st.sidebar.selectbox("Classe di rugosità", 
    ["A (Costa)", "B (Aperta campagna)", "C (Zone industriali)", "D (Centri urbani)"])
dist_mare = st.sidebar.number_input("Distanza dal mare [km]", value=5.0)

# Mappatura automatica Categoria Esposizione
if dist_mare < 1:
    cat = "A"
else:
    mapping_cat = {"A (Costa)": "B", "B (Aperta campagna)": "C", "C (Zone industriali)": "D", "D (Centri urbani)": "E"}
    cat = mapping_cat[classe_rug]
st.sidebar.warning(f"Categoria di Esposizione: **{cat}**")

# Parametri Tabella 3.3.II
params_ce = {'A': [0.16, 0.01, 2], 'B': [0.19, 0.05, 4], 'C': [0.20, 0.10, 5], 'D': [0.22, 0.30, 8], 'E': [0.23, 0.70, 12]}
kr, z0, zmin = params_ce[cat]

# --- CALCOLI ---
vb, vb0, a0 = engine.calcola_vb(zona_v, altitudine)
qb = 0.5 * engine.rho * (vb**2) / 1000
h_struttura = st.sidebar.slider("Altezza Struttura [m]", 2, 100, 15)
ce = engine.get_ce(h_struttura, kr, z0, zmin)
cp = 0.8 # Semplificato per parete sopravento
pe = qb * ce * cp

# --- LAYOUT PRINCIPALE ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Vr (Anni)", int(vr))
c2.metric("vb (m/s)", f"{vb:.2f}")
c3.metric("ce (z)", f"{ce:.3f}")
c4.metric("pe (kN/m²)", f"{pe:.3f}")

# --- SEZIONE FORMULE ---
with st.expander("🔍 Dettaglio Parametri e Formule (NTC 2018)"):
    st.write("Il calcolo segue rigorosamente le prescrizioni del Cap. 3.3:")
    st.latex(r"v_b = v_{b,0} \cdot c_a \quad \text{con } c_a = 1 \text{ se } a \le a_0")
    st.latex(r"q_b = \frac{1}{2} \rho v_b^2")
    st.latex(r"c_e(z) = k_r^2 \cdot c_t \cdot \ln(z/z_0) \cdot [7 + \ln(z/z_0)]")
    st.latex(r"p_e = q_b \cdot c_e \cdot c_p")
    
    st.markdown(f"""
    **Valori ottenuti:**
    - **Velocità base ($v_{{b,0}}$):** {vb0} m/s
    - **Altezza riferimento ($a_0$):** {a0} m
    - **Pressione base ($q_b$):** {qb:.3f} kN/m²
    - **Parametri categoria {cat}:** $k_r$={kr}, $z_0$={z0}m, $z_{{min}}$={zmin}m
    """)

# --- GRAFICI ---
st.divider()
st.subheader("📊 Analisi Grafica")
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.write("**Profilo di Pressione pe(z)**")
    z_ax = np.linspace(0, 100, 100)
    p_ax = [qb * engine.get_ce(z, kr, z0, zmin) * cp for z in z_ax]
    fig1, ax1 = plt.subplots()
    ax1.plot(p_ax, z_ax, lw=2, label=f"Cat. {cat}")
    ax1.axhline(h_struttura, color='red', ls='--', label="Quota Progetto")
    ax1.set_xlabel("Pressione [kN/m²]")
    ax1.set_ylabel("Altezza [m]")
    ax1.legend()
    st.pyplot(fig1)

with col_g2:
    st.write("**Confronto Categorie di Esposizione**")
    fig2, ax2 = plt.subplots()
    for c, p in params_ce.items():
        ce_vals = [engine.get_ce(z, p[0], p[1], p[2]) for z in z_ax]
        ax2.plot(ce_vals, z_ax, label=f"Cat. {c}")
    ax2.set_xlabel("Coefficiente ce")
    ax2.set_ylabel("Altezza [m]")
    ax2.legend()
    st.pyplot(fig2)
import numpy as np
import matplotlib.pyplot as plt

class SoftwareNTC2018:
    def __init__(self):
        # --- PARAMETRI NEVE (NTC 2018 Tab. 3.4.I) ---
        self.parametri_neve = {
            "Zona I Alpina":       {"qsk_min": 1.50, "a": 1.39, "b": 728},
            "Zona I Mediterranea": {"qsk_min": 1.50, "a": 1.35, "b": 602},
            "Zona II":             {"qsk_min": 1.00, "a": 0.85, "b": 481},
            "Zona III":            {"qsk_min": 0.60, "a": 0.51, "b": 481}
        }

        # --- PARAMETRI VENTO (NTC 2018 Tab. 3.3.I) ---
        self.parametri_vento_zona = {
            1: {"vb0": 25, "a0": 1000, "ks": 0.40},
            2: {"vb0": 25, "a0": 750,  "ks": 0.45},
            3: {"vb0": 27, "a0": 500,  "ks": 0.37},
            4: {"vb0": 28, "a0": 500,  "ks": 0.35},
            5: {"vb0": 28, "a0": 750,  "ks": 0.42},
            6: {"vb0": 28, "a0": 500,  "ks": 0.35},
            7: {"vb0": 27, "a0": 1000, "ks": 0.48},
            8: {"vb0": 28, "a0": 1250, "ks": 0.49},
            9: {"vb0": 31, "a0": 500,  "ks": 0.31}
        }

        # --- CATEGORIE DI ESPOSIZIONE (NTC 2018 Tab. 3.3.II) ---
        self.esposizione = {
            "I":   {"kr": 0.17, "z0": 0.01, "zmin": 2},
            "II":  {"kr": 0.19, "z0": 0.05, "zmin": 4},
            "III": {"kr": 0.20, "z0": 0.10, "zmin": 5},
            "IV":  {"kr": 0.22, "z0": 0.30, "zmin": 8},
            "V":   {"kr": 0.23, "z0": 0.70, "zmin": 12}
        }

    # --- LOGICA NEVE ---
    def calcola_neve(self, zona, quota_as):
        p = self.parametri_neve[zona]
        if quota_as <= 200:
            qsk = p["qsk_min"]
        else:
            qsk = p["a"] * (1 + (quota_as / p["b"])**2)
        return round(qsk, 3)

    # --- LOGICA VENTO ---
    def calcola_vento(self, zona, quota_as, altezza_z, cat_esp):
        # 1. Velocità di riferimento vb
        pz = self.parametri_vento_zona[zona]
        ca = 1.0 if quota_as <= pz["a0"] else 1 + pz["ks"] * (quota_as / pz["a0"] - 1)
        vb = pz["vb0"] * ca
        
        # 2. Pressione dinamica di riferimento qb
        rho = 1.25 # densità aria kg/m3
        qb = 0.5 * rho * (vb**2) / 1000 # in kN/mq
        
        # 3. Coefficiente di esposizione ce(z)
        esp = self.esposizione[cat_esp]
        z = max(altezza_z, esp["zmin"])
        ce = (esp["kr"] * np.log(z / esp["z0"])) * (7 + esp["kr"] * np.log(z / esp["z0"]))
        
        return {"vb": round(vb, 2), "qb": round(qb, 3), "ce": round(ce, 3)}

    # --- GENERAZIONE GRAFICI (REPLICA EXCEL) ---
    def genera_grafici(self, zona_v, quota, cat_esp, h_max=50):
        altezze = np.linspace(0.1, h_max, 100)
        pressioni = []
        coeff_esp = []
        
        for z in altezze:
            res = self.calcola_vento(zona_v, quota, z, cat_esp)
            coeff_esp.append(res["ce"])
            pressioni.append(res["qb"] * res["ce"]) # Pressione cinetica qz (cp=1.0)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

        # Grafico ce(z)
        ax1.plot(coeff_esp, altezze, 'r-', linewidth=2)
        ax1.set_title("Coeff. Esposizione $c_e(z)$")
        ax1.set_ylabel("Altezza z [m]")
        ax1.grid(True, linestyle=':')

        # Grafico Pressione p(z)
        ax2.plot(pressioni, altezze, 'b-', linewidth=2)
        ax2.set_title("Pressione del Vento $q_z$ [kN/m²]")
        ax2.set_xlabel("Pressione")
        ax2.grid(True, linestyle=':')
        
        plt.tight_layout()
        plt.show()

# --- ESEMPIO DI UTILIZZO ---
ntc = SoftwareNTC2018()

# 1. Calcolo Neve
carico_neve = ntc.calcola_neve("Zona II", 600)
print(f"❄️ Carico Neve qsk: {carico_neve} kN/mq")

# 2. Calcolo Vento
dati_vento = ntc.calcola_vento(zona=3, quota_as=400, altezza_z=15, cat_esp="III")
print(f"💨 Vento a 15m: qb={dati_vento['qb']} kN/mq, ce={dati_vento['ce']}")

# 3. Visualizzazione Grafica (Replicando i grafici del file Excel)
ntc.genera_grafici(zona_v=3, quota=400, cat_esp="III", h_max=30)
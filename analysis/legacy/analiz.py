import pandas as pd
import numpy as np

# 1. Veriyi yükle (Geant4 yorum satırlarını # ile geçer)
file_name = "DORA_Results_nt_TLD_Scoring_t0.csv"
df = pd.read_csv(file_name, comment='#', names=['TLD_ID', 'Edep_keV'])

# 2. Fiziksel Sabitler
KEV_TO_JOULE = 1.60218e-16
TLD_MASS_KG = 1.01e-4  # 7x1mm LiF pellet kütlesi

# 3. Her TLD için toplam enerjiyi hesapla ve doza çevir
results = df.groupby('TLD_ID')['Edep_keV'].sum().reset_index()
results['Dose_Gy'] = (results['Edep_keV'] * KEV_TO_JOULE) / TLD_MASS_KG

# 4. İstatistiksel özet
avg_dose = results['Dose_Gy'].mean()
print(f"--- DORA Simulation Results (10^6 events) ---")
print(f"Average Dose: {avg_dose:.4f} Gy")
print(f"Experimental Target: 1.13 Gy")
print(f"Deviation: {((avg_dose - 1.13) / 1.13 * 100):.2f}%")

# 5. 8x12 Doz Haritası Oluştur
dose_map = np.zeros((8, 12))
for _, row in results.iterrows():
    idx = int(row['TLD_ID'])
    r, c = divmod(idx, 12)
    if r < 8 and c < 12:
        dose_map[r, c] = row['Dose_Gy']

print("\n--- 8x12 Dose Map (Gy) ---")
print(pd.DataFrame(dose_map))

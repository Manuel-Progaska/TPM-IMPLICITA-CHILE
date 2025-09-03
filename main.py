import numpy as np
import pandas as pd
import math
from datetime import datetime
from pathlib import Path
from modules.bc_api import API_Client, Swaps

def dias_hasta_reuniones(fechas_rpm):
    hoy = datetime.today()
    return [(fecha, (datetime.strptime(fecha, "%Y-%m-%d") - hoy).days) for fecha in fechas_rpm]

def bootstrap_spot_curve(df_swaps, tpm_actual):
    spot = {0: tpm_actual}  # TPM actual como tasa spot para 0 días
    for _, row in df_swaps.iterrows():
        plazo = row['PLAZO']
        tasa = row['VALOR']
        spot[plazo] = tasa
    return spot

def spot_interpolada(spot, dias):
    plazos = np.array(sorted(spot.keys()))
    tasas = np.array([spot[p] for p in plazos])
    return np.interp(dias, plazos, tasas)

def tasa_forward(spot, dias_inicio, dias_fin):
    r1 = spot_interpolada(spot, dias_inicio)
    r2 = spot_interpolada(spot, dias_fin)
    t1 = dias_inicio / 360
    t2 = dias_fin / 360
    forward = ((1 + r2 * t2) / (1 + r1 * t1)) - 1
    return round(forward * 360 / (dias_fin - dias_inicio), 4)  # anualizada

def calcular_distribucion_tpm_binomial(df_swaps, fechas_rpm, tpm_actual, paso=0.25):
    """
    Calcula la matriz de probabilidad de TPM implícita para cada RPM usando modelo binomial y tasas forward.
    Args:
        df_swaps: DataFrame con columnas ['PLAZO', 'VALOR']
        fechas_rpm: lista de fechas de reuniones en formato 'yyyy-mm-dd'
        tpm_actual: valor actual de la TPM (float)
        paso: tamaño del movimiento de la TPM (default 0.25)
    Returns:
        DataFrame: matriz de probabilidades (TPM x RPM)
    """
    n = len(fechas_rpm)
    niveles_tpm = np.round(np.arange(tpm_actual - n*paso, tpm_actual + (n+1)*paso, paso), 2)
    matriz = pd.DataFrame(0.0, index=niveles_tpm, columns=fechas_rpm)

    spot = bootstrap_spot_curve(df_swaps, tpm_actual)
    dias_reuniones = dias_hasta_reuniones(fechas_rpm)

    for j, (fecha, dias) in enumerate(dias_reuniones):
        if dias <= 0:
            continue
        tasa_fwd = tasa_forward(spot, 0, dias)
        if tasa_fwd is None:
            continue

        # Nuevo enfoque: p es probabilidad de subida si tasa_fwd > tpm_actual, bajada si < tpm_actual
        if tasa_fwd >= tpm_actual:
            p_up = min(max((tasa_fwd - tpm_actual) / paso, 0), 1)
            for k, tpm in enumerate(niveles_tpm):
                num_up = int(round((tpm - tpm_actual) / paso))
                if 0 <= num_up <= (j+1):
                    prob = (math.comb(j+1, num_up) * (p_up ** num_up) * ((1-p_up) ** ((j+1)-num_up)))
                    matriz.iloc[k, j] = float(np.round(prob, 2))
        else:
            p_down = min(max((tpm_actual - tasa_fwd) / paso, 0), 1)
            for k, tpm in enumerate(niveles_tpm):
                num_down = int(round((tpm_actual - tpm) / paso))
                if 0 <= num_down <= (j+1):
                    prob = (math.comb(j+1, num_down) * (p_down ** num_down) * ((1-p_down) ** ((j+1)-num_down)))
                    matriz.iloc[k, j] = float(np.round(prob, 2))
    return matriz.sort_index(ascending=False)

if __name__ == "__main__":
    fechas_rpm = ['2025-09-09', '2025-10-28', '2025-12-16']
    tpm_actual = 4.75
    df_swaps = pd.DataFrame({
        'PLAZO': [90, 180, 360],
        'VALOR': [4.7, 4.60, 4.48]
    })
    matriz_prob = calcular_distribucion_tpm_binomial(df_swaps, fechas_rpm, tpm_actual)
    print(matriz_prob)
import numpy as np
import pandas as pd
from pathlib import Path
from modules.bc_api import API_Client, Swaps


def calcular_distribucion_tpm(df_swaps, fechas_rpm, tpm_actual):
    """
    Calcula la matriz de probabilidad de TPM implícita para cada RPM usando tasas swap.
    Args:
        df_swaps: DataFrame con columnas ['FECHA', 'PLAZO', 'VALOR']
        fechas_rpm: lista de fechas de reuniones en formato 'yyyy-mm-dd'
        tpm_actual: valor actual de la TPM (float)
    Returns:
        DataFrame: matriz de probabilidades (TPM x RPM)
    """
    # Genera posibles valores de TPM en pasos de 0.25 hacia arriba y abajo (ejemplo: +/- 1%)
    pasos = np.arange(-1.0, 1.25, 0.25)
    niveles_tpm = np.round(tpm_actual + pasos, 2)
    matriz = pd.DataFrame(0, index=niveles_tpm, columns=fechas_rpm)

    # Para cada reunión, calcula la TPM implícita usando la tasa swap del plazo correspondiente
    for fecha in fechas_rpm:
        # Busca la tasa swap del último día del mes de la reunión
        tasa_swap = df_swaps[df_swaps['FECHA'] == fecha]['VALOR'].values
        if len(tasa_swap) == 0:
            continue  # Si no hay dato, deja la columna en cero
        tasa_swap = tasa_swap[0]

        # Calcula la probabilidad para cada nivel de TPM usando una distancia inversa (más cerca, más probable)
        distancias = np.abs(niveles_tpm - tasa_swap)
        inv_dist = 1 / (distancias + 0.01)  # Evita división por cero
        probs = inv_dist / inv_dist.sum()
        matriz[fecha] = np.round(probs, 2)

    return matriz.sort_index(ascending=False)

if __name__ == "__main__":
    
    # Ejemplo de uso:
    fechas_rpm = ['2025-09-09', '2025-10-28', '2025-12-16']
    tpm_actual = 4.5
    # df_swaps debe tener las tasas swap para las fechas indicadas
    # Ejemplo ficticio:
    df_swaps = pd.DataFrame({
        'FECHA': fechas_rpm,
        'PLAZO': ['1M', '2M', '3M'],
        'VALOR': [4.75, 4.50, 4.60]
    })
    matriz_prob = calcular_distribucion_tpm(df_swaps, fechas_rpm, tpm_actual)
    print(matriz_prob)
# ...existing code...
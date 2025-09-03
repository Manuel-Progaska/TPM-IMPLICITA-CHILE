from pathlib import Path
from modules.bc_api import API_Client, Swaps

if __name__ == "__main__":

    swp = Swaps()
    cliente = API_Client()
    df_series = swp.series
    df_rates = swp.get_swaps_rates(start="2025-08-28", end="2025-08-29")

    print(df_rates)
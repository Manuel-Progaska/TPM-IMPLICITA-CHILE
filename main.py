from pathlib import Path
from modules.bc_api import API_Client, Swaps

if __name__ == "__main__":

    swp = Swaps()
    cliente = API_Client()
    df_series = swp.series
    swap2 = cliente.get_series(start="2025-08-20", end="2025-08-27", series_id="F022.SPC.TPR.D090.NO.Z.D")
    print(swap2)
import pandas as pd
import requests
from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class API_Client:
    """
    API Client to interact with the Central Bank API.
    """
    user: str = os.getenv("BC_API_USER")
    password: str = os.getenv("BC_API_PASSWORD")
    
    def search_series(self, frequency:str= 'DAILY') -> pd.DataFrame:
        """
        Search for series in the database and return SeriesInfos as a DataFrame.
        """
        url: str = f"https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx?user={self.user}&pass={self.password}&frequency={frequency}&function=SearchSeries"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if "SeriesInfos" in data and isinstance(data["SeriesInfos"], list):
                # Convert SeriesInfos to a DataFrame
                return pd.DataFrame(data["SeriesInfos"])
            else:
                raise ValueError("SeriesInfos key not found or is not a list in the API response")
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")
    
    def get_series(self, start: str = None, end: str = None, series_id: str = '-') -> pd.DataFrame:
        """
        Get series data for a given series ID and date range.
        """

        url : str = f"https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx?user={self.user}&pass={self.password}&timeseries={series_id}&firstdate={start}&lastdate={end}"
        
        print(url)
        
        response = requests.get(url)
        
    

        if response.status_code == 200:
            data_json = response.json()
            data = data_json['Series']['Obs']
            df_data = pd.DataFrame(data)
            df_data = df_data.rename(columns={"indexDateString": "FECHA", "value": "VALOR"})
            df_data.insert(1, 'ID', series_id)
            df_data.drop(columns=['statusCode'], inplace=True)
            return df_data
        else:
            raise Exception(f"Error: {response.status_code} - {response.text}")

@dataclass
class Swaps(API_Client):
    """
    Clase para manejar datos de swaps.
    """
    series : pd.DataFrame = None
    
    def __post_init__(self):
        super().__init__()
        
        # series de swaps
        self.series = self.get_swaps_series()
    
    def get_swaps_series(self):
        df_series_data : pd.DataFrame = self.search_series(frequency='DAILY')
        df_series1 : pd.DataFrame = df_series_data[df_series_data['spanishTitle'].str.contains('Swap promedio camara')]
        df_series2 : pd.DataFrame = df_series_data[df_series_data['spanishTitle'].str.contains('Swap promedio de camara')]
        df_series : pd.DataFrame = pd.concat([df_series1, df_series2]).reset_index()
        df_series = df_series.rename(columns={"seriesId": "ID", "spanishTitle": "DETALLE"})
        df_series = df_series[['ID', 'DETALLE']]
        df_series['TASA'] = df_series['ID'].apply(lambda x: x.replace(
            'F022.SPC.TIN.', 'SPC-').replace('.UF.Z.D', '-UF').replace('.NO.Z.D', '-CLP').replace('F022.SPC.TPR.', 'SPC-')
            )
    
        return df_series[['ID', 'TASA', 'DETALLE']]
    
    def get_swaps_rates(self,start:str, end:str) -> pd.DataFrame:
        """_summary_

        Args:
            satrti (_type_): _description_

        Returns:
            pd.DataFrame: _description_
        """
        df_series = self.series.copy()
        lst_df : list = []
        for serie in list(df_series['ID']):
            df_serie : pd.DataFrame = self.get_series(start=start, end=end, series_id=serie)
            rate : str = df_series[df_series['ID'] == serie]['TASA'].values[0]
            df_serie['ID'] = rate
            lst_df.append(df_serie)
        df_rates : pd.DataFrame = pd.concat(lst_df)
        df_rates['VALOR'] = pd.to_numeric(df_rates['VALOR'], errors='coerce')
        df_rates_pivot : pd.DataFrame = pd.pivot_table(df_rates, index='FECHA', columns='ID', values='VALOR', aggfunc='mean').reset_index()
        df_rates_pivot = df_rates_pivot.rename_axis(None, axis=1)
        return df_rates_pivot
        
    
import pandas as pd
from typing import Type
from pydantic import BaseModel, Field
from prophet import Prophet
from crewai.tools import tool, BaseTool
import os

from indoprimaflow.tools.tool_anomaly import ToolAnomalyInput

class IndustrialDataToolsInput(BaseModel):
    file_path: str = Field(..., description="The file path to the industrial data to be processed or forecasted.")

class IndustrialDataTools(BaseTool):
    name: str = "industrial_data_tools"
    description: str = "A tool to analyze files and give a forecast."
    input_schema: Type[BaseModel] = IndustrialDataToolsInput

    def _run(self, file_path: str) -> str:
        """
        Reads industrial data from an Excel file, prepares it for forecasting,
        and saves it to a temporary CSV file.
        """

        absolute_file_path = os.path.abspath(file_path)

        df = pd.read_excel(absolute_file_path)
        # Prepare the dataframe for Prophet
        df = df[['time', 'Cyclone_Gas_Outlet_Temp']].rename(columns={'time': 'ds', 'Cyclone_Gas_Outlet_Temp': 'y'})
        df['ds'] = pd.to_datetime(df['ds'])
        
        # Save to a temporary file and return the path
        temp_file_path = 'temp_data.csv'
        df.to_csv(temp_file_path, index=False)

        # Read the prepared data
        data = pd.read_csv(temp_file_path)
        data['ds'] = pd.to_datetime(data['ds'])

        # Train the model and forecast
        model = Prophet(changepoint_prior_scale=0.05, daily_seasonality=True)
        model.fit(data)
        future = model.make_future_dataframe(periods=576, freq='5min') # 48 hours at 5-min intervals
        forecast = model.predict(future)
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(100).to_string()
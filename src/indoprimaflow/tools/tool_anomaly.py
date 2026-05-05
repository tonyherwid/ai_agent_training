from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import pandas as pd
from sklearn.ensemble import IsolationForest

class ToolAnomalyInput(BaseModel):
    file: str = Field(..., description="The file path to analyze for anomalies.")

class Tool_anomaly(BaseTool):
    name: str = "tool_anomaly"
    description: str = "A tool to analyze files for anomalies and extract insights."
    input_schema: Type[BaseModel] = ToolAnomalyInput

    def _run(self, file: str) -> str:
        df = pd.read_excel(file, sheet_name=0)  # Assuming the file is an Excel file. You can modify this to handle different file types.
        df = df.iloc[:,1:]  # Assuming the first column is an identifier and should be excluded from analysis. Adjust as necessary.
        
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df_clean = df.dropna()
        df_clean['day_number'] = (df_clean['time']-pd.Timestamp('2000-01-01')).dt.days
        
        df_fix = df_clean.iloc[:,1:]

        iso_forest = IsolationForest(contamination=0.05,random_state=40,n_estimators=100)
        iso_forest.fit(df_fix)
        df_fix['anomaly'] = iso_forest.predict(df_fix)
        anomaly_count = (df_fix['anomaly'] == -1).sum()
        total_data = len(df_fix)

        dataReturn = {
            "anomali": anomaly_count,
            "total_data": total_data,
        }
        
        return dataReturn
        # Implement your anomaly analysis logic here
        # For demonstration, we'll return a dummy insight
        #return f"Analyzed {file} and found the following anomalies: [Dummy Insight]"
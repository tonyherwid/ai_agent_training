import os
from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import mysql.connector

class SaveToDBToolInput(BaseModel):
    head: int = Field(..., description="The data to be saved to the database.")
    helmet: int = Field(..., description="The data to be saved to the database.")
    person: int = Field(..., description="The data to be saved to the database.")

class SaveToDBTool(BaseTool):
    name: str = "save_to_db_tool"
    description: str = "A tool to save data to the database."
    input_schema: Type[BaseModel] = SaveToDBToolInput

    def _run(self, head: int, helmet: int, person: int) -> str:
        try:
            connect = mysql.connector.connect(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASS"),
                database="helmet_report"
            )
            cursor = connect.cursor()

            if(head > 0 or helmet > 0 or person > 0):
                detail = f"Data to be saved: head={head}, helmet={helmet}, person={person}"
                query = "INSERT INTO helmet_report (report_result, report_detected) VALUES (%s, %s)"
                values = (detail, 1)
                cursor.execute(query, values)
                connect.commit()
                return f"Data saved to database: head={head}, helmet={helmet}, person={person}"
            else:
                return "No data to save to database: head=0, helmet=0, person=0"
        except mysql.connector.Error as err:
            return f"Error occurred while saving data to database: {err}"
        finally:
            if connect.is_connected():
                cursor.close()
                connect.close()
        #return f"Data saved to database: head={head}, helmet={helmet}, person={person}"
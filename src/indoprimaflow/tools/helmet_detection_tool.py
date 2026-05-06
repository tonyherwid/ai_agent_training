from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from ultralytics import YOLO

class HelmetDetectionToolInput(BaseModel):
    file_path: str = Field(..., description="The file path to the image to be analyzed for helmet detection.")

class HelmetDetectionTool(BaseTool):
    name: str = "helmet_detection_tool"
    description: str = "A tool to analyze images for helmet detection and extract insights."
    input_schema: Type[BaseModel] = HelmetDetectionToolInput

    modelYolo: YOLO = YOLO("/Users/tonyhw/Documents/AI Training/project/indoprimaflow/src/indoprimaflow/tools/yolo_model_best_trained.pt")

    def _run(self, file_path: str) -> str:        
        result = self.modelYolo.predict(file_path)
        detected_objects = result[0].boxes.cls.tolist()
        class_names = result[0].names
        
        head = 0
        helmet = 0
        person = 0

        for hasil in detected_objects:
            if hasil == 0:
                head += 1
            elif hasil == 1:
                helmet += 1
            else:
                person += 1

        result_dict = {
            "result": f"Analyzed {file_path} and detected the following helmets: {helmet}, heads: {head}, and persons: {person}.",
            "head": head,
            "helmet": helmet,
            "person": person
        }

        return str(result_dict)
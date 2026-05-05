from tasks.celery_app import celery_app
from src.indoprimaflow.crews.content_crew.content_crew import ContentCrew
from src.indoprimaflow.crews.analyzer.analyzer import Analyzer
from src.indoprimaflow.crews.sa_crew.sa_crew import SaCrew
from src.indoprimaflow.crews.dev_crew.dev_crew import DevCrew
from src.indoprimaflow.crews.file_analyzer.file_analyzer import FileAnalyzer
from src.indoprimaflow.crews.json_analyzer.json_analyzer import JsonAnalyzer
from src.indoprimaflow.crews.excel_analyzer.excel_analyzer import ExcelAnalyzer
from src.indoprimaflow.crews.anomaly_crew.anomaly_crew import AnomalyCrew
import logging
import traceback

logger = logging.getLogger(__name__)

@celery_app.task(name="research", bind=True)
def research(self, topic:str, style:str):
    self.update_state(state="RUNNING", meta={"current":f"start job for {topic} with {style} wording style"})
    try:
        result = ContentCrew().crew().kickoff(inputs={"topic": topic, "style": style})
        return str(result)
    except Exception as e:
        logger.error(f"Error in research task: {e}")
        logger.error(traceback.format_exc())
        raise e

@celery_app.task(name="market_research", bind=True)
def market_research(self, topic:str, style:str, current_year:str):
    self.update_state(state="RUNNING", meta={"current":f"start job for {topic} with {style} wording style on current year {current_year}"})
    try:
        result = Analyzer().crew().kickoff(inputs={"topic": topic, "style": style, "current_year": current_year})
        return str(result)
    except Exception as e:
        logger.error(f"Error in market_research task: {e}")
        logger.error(traceback.format_exc())
        raise e

@celery_app.task(name="system_analyst", bind=True)
def system_analyst(self, topic:str, style:str):
    self.update_state(state="RUNNING", meta={"current":f"start job for {topic} with {style} wording style"})
    try:
        result = SaCrew().crew().kickoff(inputs={"topic": topic, "style": style})
        return str(result)
    except Exception as e:
        logger.error(f"Error in system_analyst task: {e}")
        logger.error(traceback.format_exc())
        raise e
    
@celery_app.task(name="development", bind=True)
def development(self, topic:str, language:str):
    self.update_state(state="RUNNING", meta={"current":f"start job for {topic} with {language} programming language"})
    try:
        result = DevCrew().crew().kickoff(inputs={"topic": topic, "language": language})
        return str(result)
    except Exception as e:
        logger.error(f"Error in development task: {e}")
        logger.error(traceback.format_exc())
        raise e
    
@celery_app.task(name="txt_file_analyzer", bind=True)
def txt_file_analyzer(self, file:str):
    self.update_state(state="RUNNING", meta={"current":f"start job for {file}"})
    try:
        result = FileAnalyzer().crew().kickoff(inputs={"file": file})
        return result.json_dict
    except Exception as e:
        logger.error(f"Error in txt_file_analyzer task: {e}")
        logger.error(traceback.format_exc())
        raise e
    
@celery_app.task(name="json_file_analyzer", bind=True)
def json_file_analyzer(self, file:str):
    self.update_state(state="RUNNING", meta={"current":f"start job for {file}"})
    try:
        result = JsonAnalyzer().crew().kickoff(inputs={"file": file})
        return result.json_dict
    except Exception as e:
        logger.error(f"Error in json_file_analyzer task: {e}")
        logger.error(traceback.format_exc())
        raise e
    
@celery_app.task(name="excel_file_analyzer", bind=True)
def excel_file_analyzer(self, file:str):
    self.update_state(state="RUNNING", meta={"current":f"start job for {file}"})
    try:
        result = ExcelAnalyzer().crew().kickoff(inputs={"file": file})
        return result.json_dict
    except Exception as e:
        logger.error(f"Error in excel_file_analyzer task: {e}")
        logger.error(traceback.format_exc())
        raise e
    
@celery_app.task(name="anomaly_detection", bind=True)
def anomaly_detection(self, file:str):
    self.update_state(state="RUNNING", meta={"current":f"start job for {file}"})
    try:
        result = AnomalyCrew().crew().kickoff(inputs={"file": file})
        return result.json_dict
    except Exception as e:
        logger.error(f"Error in anomaly_detection task: {e}")
        logger.error(traceback.format_exc())
        raise e
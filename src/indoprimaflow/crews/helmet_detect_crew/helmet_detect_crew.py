from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from pydantic import BaseModel
from src.indoprimaflow.tools.helmet_detection_tool import HelmetDetectionTool
from src.indoprimaflow.tools.save_to_db_tool import SaveToDBTool
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class HelmetDetectCrew():
    """HelmetDetectCrew crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    class Output_helmet_detect(BaseModel):
        result: str
        head: int
        helmet: int
        person: int

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'], # type: ignore[index]
            verbose=True,
            tools=[HelmetDetectionTool()], # Add your tool here
        )
    
    @agent
    def analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['analyzer'], # type: ignore[index]
            verbose=True,
            tools=[SaveToDBTool()], # Add your tool here
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'], # type: ignore[index]
            output_file='output/helmet_detect_file.md',
            output_json=self.Output_helmet_detect # This will create a JSON schema for the expected output, which can be used for validation and structured output parsing
        )
    
    @task
    def analyzer_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyzer_task'], # type: ignore[index]
            output_file='output/helmet_analyzer_file.md',
        )

    @crew
    def crew(self) -> Crew:
        """Creates the HelmetDetectCrew crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )

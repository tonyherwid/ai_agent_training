from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from src.indoprimaflow.tools.prophet_tool import IndustrialDataTools
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class ProphetCrew():
    """ProphetCrew crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def data_preparation_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['data_preparation_specialist'], # type: ignore[index]
            tools=[IndustrialDataTools.read_and_prepare_industrial_data],
            verbose=True
        )

    @agent
    def prophet_forecasting_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['prophet_forecasting_specialist'], # type: ignore[index]
            tools=[IndustrialDataTools.run_prophet_forecast_from_file],
            verbose=True
        )
    
    @agent
    def industrial_insight_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['industrial_insight_analyst'], # type: ignore[index]
            verbose=True
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def data_preprocessing_task(self) -> Task:
        return Task(
            config=self.tasks_config['data_preprocessing_task'], # type: ignore[index]
        )

    @task
    def model_training_and_forecasting(self) -> Task:
        return Task(
            config=self.tasks_config['model_training_and_forecasting'], # type: ignore[index]
        )

    @task
    def final_analysis_report(self) -> Task:
        return Task(
            config=self.tasks_config['final_analysis_report'], # type: ignore[index]
            output_file='report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the ProphetCrew crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
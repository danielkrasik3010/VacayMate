from typing import Any, Dict
from langgraph.graph import StateGraph, START, END
import sys
import os

# Make sure the repository root (parent of "code") is on sys.path when running.
# This helps absolute imports like "from code.states..." work reliably when running as a module.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Prefer absolute package imports
from states.VacayMate_state import VacationPlannerState
from consts import (
    MANAGER,
    RESEARCHER,
    CALCULATOR,
    PLANNER,
    SUMMARIZER,
    MERGE_RESULTS,
)
from nodes.VacayMate_nodes import (
    make_manager_node,
    make_researcher_node,
    make_calculator_node,
    make_planner_node,
    make_summarizer_node,
    make_merge_node,
)


def build_vacation_graph(config: Dict[str, Any]) -> StateGraph:
    """
    Build the VacationPlanner agent workflow graph.

    Flow:
        START -> Manager -> Researcher -> (Calculator + Planner in parallel)
        -> MERGE -> Summarizer -> END
    """
    graph = StateGraph(VacationPlannerState)

    # Get agent configurations or use defaults
    agents_config = config.get("agents_config", {})
    llm = config.get("llm", "gpt-4o-mini")
    temperature = config.get("temperature", 0.3)
    max_tokens = config.get("max_tokens", 4000)

    # ---------------------- ADD NODES ----------------------
    manager_config = agents_config.get("manager", {})
    manager_node = make_manager_node(
        llm=manager_config.get("llm", llm),
        prompt_cfg=manager_config.get("prompt_config", {})
    )
    graph.add_node(MANAGER, manager_node)

    researcher_config = agents_config.get("researcher", {})
    researcher_node = make_researcher_node(
        llm=researcher_config.get("llm", llm),
        tools=researcher_config.get("tools", []),
        prompt_cfg=researcher_config.get("prompt_config", {})
    )
    graph.add_node(RESEARCHER, researcher_node)

    calculator_config = agents_config.get("calculator", {})
    calculator_node = make_calculator_node(
        llm=calculator_config.get("llm", llm),
        tools=calculator_config.get("tools", []),
        prompt_cfg=calculator_config.get("prompt_config", {})
    )
    graph.add_node(CALCULATOR, calculator_node)

    planner_config = agents_config.get("planner", {})
    planner_node = make_planner_node(
        llm=planner_config.get("llm", llm),
        tools=planner_config.get("tools", []),
        prompt_cfg=planner_config.get("prompt_config", {})
    )
    graph.add_node(PLANNER, planner_node)

    # Use the new make_merge_node function
    merge_node = make_merge_node(llm=llm, tools=[], prompt_cfg={})
    graph.add_node(MERGE_RESULTS, merge_node)
    
    summarizer_config = agents_config.get("summarizer", {})
    summarizer_node = make_summarizer_node(
        llm=summarizer_config.get("llm", llm),
        tools=[],
        prompt_cfg=summarizer_config.get("prompt_config", {})
    )
    graph.add_node(SUMMARIZER, summarizer_node)

    # ---------------------- ADD EDGES ----------------------
    graph.add_edge(START, MANAGER)
    graph.add_edge(MANAGER, RESEARCHER)

    # Both Calculator and Planner run in parallel after Researcher
    graph.add_edge(RESEARCHER, CALCULATOR)
    graph.add_edge(RESEARCHER, PLANNER)

    # Both Calculator and Planner now feed into the MERGE node
    graph.add_edge(CALCULATOR, MERGE_RESULTS)
    graph.add_edge(PLANNER, MERGE_RESULTS)
    
    # The MERGE node feeds into the Summarizer
    graph.add_edge(MERGE_RESULTS, SUMMARIZER)
    
    graph.add_edge(SUMMARIZER, END)

    # ---------------------- COMPILE ------------------------
    return graph.compile()

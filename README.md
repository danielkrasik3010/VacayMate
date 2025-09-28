
# VacayMate - Reliable AI Travel Planning System
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![LangChain](https://img.shields.io/badge/LangChain-0.3+-green.svg)](https://langchain.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.4+-purple.svg)](https://langgraph.com)

VacayMate is a travel planning system designed to take the stress out of organizing your next trip. What started as a simple experiment has grown into a robust, production-ready platform that handles the research, calculations, and details for you. The new version is focused on reliability, resilience, and a smooth user experience—so you can focus on enjoying your vacation, not worrying about logistics.

## What Makes VacayMate Different?

VacayMate is not just another booking tool. It’s a digital travel companion that coordinates all the moving parts of your trip, checks its own work, and recovers gracefully from errors. The system is built around a set of defensive programming patterns that ensure it keeps running smoothly, even when things go wrong with external APIs or data sources.

### Key Features

- Multi-agent architecture for research, planning, cost calculation, and summarization
- Defensive programming patterns for reliability and error recovery
- Real-time monitoring and dashboards
- Streamlit-based user interface and system dashboard
- Automatic recovery from failures and outages
- Health metrics and clear error reporting
- Configuration-driven and easy to customize

## Defensive Patterns: How Reliability is Built In

VacayMate’s production system uses six core defensive programming patterns:

1. **Resilient Output Parsing and Schema Validation**: Every API response is validated to ensure data consistency and catch malformed responses. Fallback values are used if something is missing.
2. **Circuit Breakers and Tool-Level Fallbacks**: The system monitors API failures and temporarily disables failing services to prevent cascading errors.
3. **State Validation and Recovery Safeguards**: State is validated before and after each step, with automatic repair and emergency state creation if needed.
4. **Iteration Caps and Loop Detection**: Prevents infinite loops and runaway processes with state fingerprinting and iteration limits.
5. **Exponential Backoff and Retry Logic**: Automatically retries failed API calls with intelligent backoff strategies.
6. **Resource Usage Limits and Tool Sandboxing**: Monitors memory and execution time, and isolates risky operations.

## System Overview

VacayMate is built around five specialized agents:

- **Manager**: Orchestrates the process, checks your input, and ensures everything happens in the right order.
- **Researcher**: Gathers real-time data on flights, hotels, and attractions, handling API hiccups with fallbacks and retries.
- **Calculator**: Crunches the numbers and ensures costs are clear and accurate.
- **Planner**: Builds your day-by-day itinerary, taking into account weather, events, and your preferences.
- **Summarizer**: Pulls everything together into a clean, readable plan.

### Workflow Diagram

```
      ┌─────────────┐
      │   START     │
      └──────┬──────┘
             │
             ▼
      ┌─────────────┐
      │   MANAGER   │
      │   AGENT     │
      └──────┬──────┘
             │
             ▼
      ┌─────────────┐
      │ RESEARCHER  │
      │   AGENT     │
      └──────┬──────┘
             │
        ┌────┴────┐
        ▼         ▼
   ┌──────────┐ ┌──────────┐
   │CALCULATOR│ │ PLANNER  │
   │  AGENT   │ │  AGENT   │
   └────┬─────┘ └─────┬────┘
        │             │
        └──────┬──────┘
               ▼
      ┌─────────────┐
      │ SUMMARIZER  │
      │   AGENT     │
      └──────┬──────┘
             │
             ▼
      ┌─────────────┐
      │     END     │
      └─────────────┘
```

## Core Agents

### Manager Agent (`VacayMate_nodes.py`)

- **Role**: Workflow orchestrator and input validator
- **Responsibilities**: 
  - Parse and validate user requests
  - Extract travel dates, locations, and preferences
  - Route tasks to appropriate specialized agents
  - Ensure workflow completion in correct sequence

---

### Researcher Agent (`VacayMate_nodes.py`)

- **Role**: Data collection and research specialist
- **Tools Used**: 
  - Flight Prices Tool
  - Hotel Prices Tool  
  - Destination Info Tool
- **Responsibilities**:
  - Find flight options and prices
  - Research hotel availability and rates
  - Gather destination information and attractions

---

### Calculator Agent (`VacayMate_nodes.py`)

- **Role**: Financial analysis and cost computation
- **Tools Used**: Make Quotation Tool
- **Responsibilities**:
  - Calculate total vacation costs
  - Generate detailed cost breakdowns
  - Apply commission rates
  - Provide cost summaries with lowest/highest options

---

### Planner Agent (`VacayMate_nodes.py`)

- **Role**: Itinerary creation and scheduling
- **Tools Used**: 
  - Weather Forecast Tool
  - Event Finder Tool
- **Responsibilities**:
  - Create day-by-day itineraries
  - Integrate weather forecasts
  - Find and include local events
  - Optimize activity scheduling

---

### Summarizer Agent (`VacayMate_nodes.py`)

- **Role**: Final document generation and presentation
- **Responsibilities**:
  - Combine all agent outputs
  - Generate polished vacation plans
  - Format professional travel documents
  - Save plans to markdown files

---

## Tools & Integrations

### Flight Prices Tool (`Flights_prices_tool.py`)

- **API**: SerpAPI Google Flights
- **Functionality**: Real-time flight search and pricing
- **Features**: Round-trip flights, multiple airlines, seat availability

### Hotel Prices Tool (`Hotels_prices_tool.py`)

- **API**: SerpAPI Google Hotels
- **Functionality**: Hotel search and booking information
- **Features**: Price comparison, ratings, amenities, location data

### Weather Forecast Tool (`Weather_Forecast_tool.py`)

- **API**: OpenWeatherMap
- **Functionality**: 5-day weather forecasts
- **Features**: Temperature, conditions, humidity, wind speed

### Event Finder Tool (`Event_finder_tool.py`)

- **API**: SerpAPI Google Events
- **Functionality**: Local event discovery
- **Features**: Date-filtered events, venues, ticket information

### Quotation Tool (`Make_quotation_tool.py`)

- **Functionality**: Cost calculation and quotation generation
- **Features**: 
  - Hotel and flight cost aggregation
  - Daily expense estimation via LLM
  - Commission calculation (10%)
  - Detailed cost breakdowns

### Destination Info Tool (`destination_info_tool.py`)

- **API**: Tavily Search
- **Functionality**: Destination research and information gathering
- **Features**: Attractions, activities, local insights

---

## Configuration

### Configuration Structure (`config/config.yaml`)

```yaml
vacaymate_system:
  max_retries: 3
  timeout_seconds: 300
  max_search_queries: 5
  max_hotels: 10
  max_events: 10
  
  # Model configuration for all agents
  model_config:
    temperature: 0.3
    max_tokens: 4000
    top_p: 1.0

  agents:
    manager:
      llm: gpt-4o-mini
      prompt_config:
        role: Vacation Manager & Orchestrator
        instruction: |
          You are the central manager of the VacayMate system...
        output_constraints:
          - Return structured, validated input
        goal: Orchestrate the full vacation planning workflow
    
    researcher:
      llm: gpt-4o-mini
      tools:
        - get_destination_info
        - get_flight_prices
        - hotel_search
      prompt_config:
        role: Data Researcher for vacation planning
        # ... detailed prompts for each agent
```
## System Workflow

1. **Input Processing**: User provides trip details
2. **Research Phase**: Gather flights, hotels, and destination info
3. **Planning Phase**: Create itinerary with weather and events
4. **Cost Analysis**: Calculate comprehensive pricing
5. **Summarization**: Compile final vacation plan
6. **Export**: Generate downloadable Markdown report

## Quick Start

**Requirements:**
- Python 3.8+
- API keys for OpenAI/Groq, Tavily, SerpAPI, RapidAPI, and OpenWeatherMap

**Setup:**
1. Clone the repository:
  ```bash
  git clone https://github.com/danielkrasik3010/VacayMate.git
  cd VacayMate
  **move to prod branch**
  ```
2. Create a virtual environment:
  ```bash
  python -m venv venv
  # On Windows:
  venv\Scripts\activate
  # On Mac/Linux:
  source venv/bin/activate
  ```
3. Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```
4. Set up your environment variables in a `.env` file:
  ```env
  OPENAI_API_KEY=your_openai_key
  GROQ_API_KEY=your_groq_key
  TAVILY_API_KEY=your_tavily_key
  SERPAPI_API_KEY=your_serpapi_key
  FLIGHTS_RAPID_API_KEY=your_rapidapi_key
  OWM_API_KEY=your_openweather_key
  ```
5. Run the production UI (recommended):
  ```bash
  streamlit run UI/app_defensive.py
  ```
  Or run the dashboard for monitoring:
  ```bash
  streamlit run UI/dashboard.py
  ```

## Project Structure

```
VacayMate/
├── code/
│   ├── tools/                  # Tools for flights, hotels, weather, events, etc.
│   ├── nodes/                  # Node logic (defensive and standard)
│   ├── graphs/                 # Workflow graphs
│   ├── states/                 # State management (defensive and standard)
│   ├── VacayMate_system.py     # Original system
│   └── VacayMate_system_production.py  # Production-ready defensive system
├── UI/                        # Streamlit UIs and dashboard
├── config/                    # Configuration files
├── outputs/                   # Generated vacation plans
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

## Using the Production System

The new production-ready system is available in `code/VacayMate_system_production.py` and is designed for reliability and monitoring. Here’s a simple example:

```python
from VacayMate_system_production import ProductionVacayMate

vacay_mate = ProductionVacayMate(
   llm_model="gpt-4o-mini",
   enable_monitoring=True
)

result = vacay_mate.run(
   user_request="Plan a 7-day romantic trip to Paris",
   export_formats='markdown'
)
```

## Configuration

All system behavior is controlled by `config/config.yaml`. You can adjust agent prompts, model parameters, tool assignments, and system limits without changing the code. API keys are loaded from environment variables for security.

## User Interface and Monitoring

VacayMate comes with a modern Streamlit UI (`UI/app_defensive.py`) and a real-time dashboard (`UI/dashboard.py`). The dashboard provides:
- System health and uptime
- Circuit breaker status for all external services
- Performance metrics and error logs
- Resource usage and alerts

## Contributing

Contributions are welcome! Please open an issue or pull request if you have ideas, bug reports, or improvements.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

##  Acknowledgments

- Built with [LangChain](https://langchain.com) and [LangGraph](https://langgraph.com)
- UI powered by [Streamlit](https://streamlit.io)
- Data sources: Tavily, SerpAPI, RapidAPI, OpenWeatherMap
- AI models: OpenAI GPT-4, Groq Mixtral

## Support

For questions, issues, or contributions:
- 🐛 [Report bugs](https://github.com/danielkrasik3010/VacayMate/issues)
- 💡 [Request features](https://github.com/danielkrasik3010/VacayMate/issues)
- 📧 Contact: [GitHub Profile](https://github.com/danielkrasik3010)

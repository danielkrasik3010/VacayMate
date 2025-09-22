from typing import List, TypedDict, Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph.message import AnyMessage, add_messages
from typing_extensions import Annotated

# ---------------- FLIGHTS ---------------- #
class FlightLeg(BaseModel):
    source: str
    sourceCode: str
    destination: str
    destinationCode: str
    departureLocalTime: str
    arrivalLocalTime: str
    carrier: str
    carrierCode: str
    cabinClass: str
    summary: str

class FlightItinerary(BaseModel):
    id: str
    priceUSD: float
    priceEUR: float
    durationOutbound: str
    durationInbound: str
    lastAvailableSeats: int
    outbound: FlightLeg
    inbound: FlightLeg
    bookingUrl: str
    human_readable_summary: str

class FlightSearchResult(BaseModel):
    itineraries: List[FlightItinerary] = Field(default_factory=list)

# ---------------- HOTELS ---------------- #
class HotelPrice(BaseModel):
    per_night: str
    per_night_value: float
    total: str
    total_value: float

class HotelAddress(BaseModel):
    latitude: float
    longitude: float
    formatted: str

class Hotel(BaseModel):
    name: str
    description: Optional[str] = None
    rating: Optional[float] = None
    hotel_class: Optional[str] = None
    price: HotelPrice
    address: HotelAddress
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    summary: str

# Updated to match the JSON output from the tool
class HotelSearchResult(BaseModel):
    query: str
    check_in_date: str
    check_out_date: str
    total_found: int = 0
    hotels: List[Hotel] = Field(default_factory=list)

# ---------------- ATTRACTIONS ---------------- #
class Attraction(BaseModel):
    name: str
    description: str
    type: str
    location: str

# ---------------- EVENTS ---------------- #
class EventDate(BaseModel):
    start_date: str
    when: str

class Event(BaseModel):
    title: str
    date: EventDate
    venue: Optional[str] = None
    link: str

# ---------------- WEATHER ---------------- #
class WeatherForecast(BaseModel):
    date: str
    condition: str
    temp_high: float
    temp_low: float
    wind_speed: float
    humidity: int
    precipitation: float

class WeatherForecastResult(BaseModel):
    forecasts: List[WeatherForecast] = Field(default_factory=list)
    human_readable_summary: str

# ---------------- RESEARCH RESULTS ---------------- #
class ResearchResults(BaseModel):
    """Raw data collected by Researcher agent."""
    flights: FlightSearchResult = Field(default_factory=FlightSearchResult)
    accommodations: HotelSearchResult = Field(default_factory=HotelSearchResult)
    attractions: List[Attraction] = Field(default_factory=list)
    tavily_research: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

# ---------------- PLANNER RESULTS ---------------- #
class PlannerResults(BaseModel):
    """Processed itinerary data from Planner agent."""
    weather_forecast: Optional[WeatherForecastResult] = None
    local_events: List[Event] = Field(default_factory=list)

# ---------------- CALCULATOR RESULTS ---------------- #
class CalculatorResults(BaseModel):
    """Financial outputs from Calculator agent."""
    quotation: Dict[str, Any] = Field(default_factory=dict)

# ---------------- AGENT PROMPTS ---------------- #
class AgentPromptConfig(BaseModel):
    role: str
    instruction: str
    output_constraints: List[str] = Field(default_factory=list)
    goal: str

# ---------------- STATE ---------------- #
class VacationPlannerState(TypedDict):
    # User input - these should not be modified after initialization
    user_request: str
    current_location: str
    destination: str
    travel_dates: str
    start_date: str
    return_date: str

    # Agent message histories - use add_messages for safe concurrent updates
    manager_messages: Annotated[List[str], add_messages]
    researcher_messages: Annotated[List[str], add_messages]
    calculator_messages: Annotated[List[str], add_messages]
    planner_messages: Annotated[List[str], add_messages]
    summarizer_messages: Annotated[List[str], add_messages]

    # Agent outputs - these should be updated by single agents only
    research_results: Dict[str, Any]
    planner_results: Dict[str, Any]
    calculator_results: Dict[str, Any]

    # Prompts from config - should not be modified after initialization
    manager_prompt: Dict[str, Any]
    researcher_prompt: Dict[str, Any]
    calculator_prompt: Dict[str, Any]
    planner_prompt: Dict[str, Any]
    summarizer_prompt: Dict[str, Any]
    
    # Tools available to agents - should not be modified after initialization
    tools: List[Dict[str, Any]]

    # Drafts and final outputs - updated by single agents only
    itinerary_draft: str
    final_plan: str
    plan_approved: bool

# ---------------- INITIALIZATION ---------------- #
def initialize_vacation_state(
    user_request: str = "",
    current_location: str = "",
    destination: str = "",
    start_date: str = "",
    return_date: str = "",
    manager_prompt_cfg: Optional[dict] = None,
    researcher_prompt_cfg: Optional[dict] = None,
    calculator_prompt_cfg: Optional[dict] = None,
    planner_prompt_cfg: Optional[dict] = None,
    summarizer_prompt_cfg: Optional[dict] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
) -> VacationPlannerState:
    """Initialize the VacayMate state with default values."""
    # Create a dict that matches the TypedDict structure
    return {
        "user_request": user_request or "",
        "current_location": current_location or "",
        "destination": destination or "",
        "travel_dates": f"{start_date} to {return_date}" if start_date and return_date else "",
        "start_date": start_date or "",
        "return_date": return_date or "",
        "manager_messages": [],
        "researcher_messages": [],
        "calculator_messages": [],
        "planner_messages": [],
        "summarizer_messages": [],
        "research_results": {},
        "planner_results": {},
        "calculator_results": {},
        "manager_prompt": manager_prompt_cfg or {},
        "researcher_prompt": researcher_prompt_cfg or {},
        "calculator_prompt": calculator_prompt_cfg or {},
        "planner_prompt": planner_prompt_cfg or {},
        "summarizer_prompt": summarizer_prompt_cfg or {},
        "tools": tools or [],
        "itinerary_draft": "",
        "final_plan": "",
        "plan_approved": False
    }

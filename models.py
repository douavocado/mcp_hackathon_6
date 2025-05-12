from typing import List, Optional, Set
from pydantic import BaseModel, Field

class Geolocation(BaseModel):
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    
    model_config = {"extra": "forbid"}

class RestaurantInfo(BaseModel):
    name: str = Field(..., description="Name of the restaurant")
    type: str = Field(..., description="Type of restaurant (e.g., pub, cafe)")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    
    model_config = {"extra": "forbid"}

class RouteDetails(BaseModel):
    distance: str = Field(..., description="Distance between locations")
    directions: str = Field(..., description="Brief directions between locations")
    
    model_config = {"extra": "forbid"}

class RestaurantSelection(BaseModel):
    selected_meals: List[str] = Field(..., description="List of meal types selected (breakfast, lunch, dinner)")
    breakfast_restaurant: Optional[RestaurantInfo] = Field(None, description="Details of the selected breakfast restaurant")
    lunch_restaurant: Optional[RestaurantInfo] = Field(None, description="Details of the selected lunch restaurant")
    dinner_restaurant: Optional[RestaurantInfo] = Field(None, description="Details of the selected dinner restaurant")
    selection_reasoning: str = Field(..., description="Explanation of why these restaurants were selected based on user preferences")
    
    model_config = {"extra": "forbid"}

class TravelTimes(BaseModel):
    breakfast_to_lunch: Optional[str] = Field(None, description="Estimated travel time from breakfast to lunch")
    lunch_to_dinner: Optional[str] = Field(None, description="Estimated travel time from lunch to dinner")
    breakfast_to_dinner: Optional[str] = Field(None, description="Estimated travel time from breakfast to dinner")
    
    model_config = {"extra": "forbid"}

class RoutePlan(BaseModel):
    route_overview: str = Field(..., description="Brief overview of the full day's route")
    selected_meals: List[str] = Field(..., description="List of meal types selected (breakfast, lunch, dinner)")
    breakfast_to_lunch: Optional[RouteDetails] = Field(None, description="Route details from breakfast to lunch location")
    lunch_to_dinner: Optional[RouteDetails] = Field(None, description="Route details from lunch to dinner location")
    breakfast_to_dinner: Optional[RouteDetails] = Field(None, description="Route details from breakfast to dinner location")
    transport_recommendations: List[str] = Field(..., description="List of recommended transportation methods")
    travel_times: TravelTimes = Field(..., description="Estimated travel times between locations")
    
    model_config = {"extra": "forbid"}

class CompanionOutput(BaseModel):
    greeting: str = Field(..., description="Friendly greeting to the user")
    day_overview: str = Field(..., description="Overview of the day's eating and travel plan")
    restaurant_highlights: str = Field(..., description="Highlights of each selected restaurant")
    route_guidance: str = Field(..., description="Clear explanation of the route between restaurants")
    closing_remarks: str = Field(..., description="Friendly closing remarks")
    
    model_config = {"extra": "forbid"}
    
    def format(self) -> str:
        return "\n\n".join([
            f"**Hello!** {self.greeting}",
            f"**Your Cambridge Food Day:**\n{self.day_overview}",
            f"**Restaurant Highlights:**\n{self.restaurant_highlights}",
            f"**Getting Around:**\n{self.route_guidance}",
            f"{self.closing_remarks}"
        ]) 
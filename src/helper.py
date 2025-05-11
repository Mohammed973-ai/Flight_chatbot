from amadeus import Client, ResponseError
from typing import Optional, List
from dotenv import load_dotenv 
import os
load_dotenv()
amadeus_api_key= os.getenv("AMADEUS_API_KEY")
amadeus_api_secret = os.getenv("AMADEUS_API_SECRET")
amadeus = Client(
    client_id = amadeus_api_key,
    client_secret = amadeus_api_secret
)
def search_flights(
    originLocationCode: str ,
    destinationLocationCode: str ,
    departureDate: str ,
    max: int = 4,
    returnDate: Optional[str] = None,
    adults: int = 1,
    children: Optional[int] = None,
    infants: Optional[int] = None,
    travelClass: Optional[str] = None,
    currencyCode: Optional[str] = None,
    nonStop: Optional[bool] = None,
    includedAirlineCodes: Optional[List[str]] = None,
    excludedAirlineCodes: Optional[List[str]] = None,
    maxPrice: Optional[int] = None
) -> str:
    """
    Search flights using Amadeus API and
    ARGS:
     # --- Mandatory fields ---
    originLocationCode: str = Field(description="Origin airport IATA code (e.g., 'LAX')")
    destinationLocationCode: str = Field(description="Destination airport IATA code (e.g., 'JFK')")
    departureDate: str = Field(description="Departure date in format YYYY-MM-DD")
    max: int = Field(default=250, description="Maximum number of flight offers to return")
    # --- Optional fields ---
    returnDate: Optional[str] = Field(default=None, description="Return date for round trips (YYYY-MM-DD)")
    adults:Optional[int] = Field(default = 1,description="Number of adult passengers")
    children: Optional[int] = Field(default=None, description="Number of children passengers")
    infants: Optional[int] = Field(default=None, description="Number of infant passengers")
    travelClass: Optional[str] = Field(default=None, description="Travel class: ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST")
    currencyCode: Optional[str] = Field(default=None, description="Preferred currency for prices (e.g., USD)")
    nonStop: Optional[str] = Field(default=None, description="True if only nonstop flights are preferred")
    includedAirlineCodes: Optional[List[str]] = Field(default=None, description="List of airline IATA codes to include")
    excludedAirlineCodes: Optional[List[str]] = Field(default=None, description="List of airline IATA codes to exclude")
    maxPrice: Optional[int] = Field(default=None, description="Maximum price for flight offers")
    returns:
    if no flights returned tell th user that you couldnt find flights from origin to destination on date
    if an error occued tell the user that your sorry you are running in some issues
    if there are flights return the flights information like Flight number,Origin (departure),Destination (arrival)
    Flight duration,Price,and keep other information so that if user asked you
    about them
    """
    try:
        params = {
            "originLocationCode": originLocationCode,
            "destinationLocationCode": destinationLocationCode,
            "departureDate": departureDate,
            "returnDate": returnDate,
            "adults": adults,
            "children": children,
            "infants": infants,
            "travelClass": travelClass,
            "includedAirlineCodes": ",".join(includedAirlineCodes) if includedAirlineCodes else None,
            "excludedAirlineCodes": ",".join(excludedAirlineCodes) if excludedAirlineCodes else None,
            "nonStop": nonStop,
            "currencyCode": currencyCode,
            "maxPrice": maxPrice,
            "max": max,
        }
        params = {k: v for k, v in params.items() if v is not None}
        response = amadeus.shopping.flight_offers_search.get(**params)
        results = response.data

        if not results:
            return f"No flights found from {originLocationCode} to {destinationLocationCode} on {departureDate}."

        output = f"✈️ Flight options from {originLocationCode} to {destinationLocationCode} on {departureDate}:\n\n"

        for i, offer in enumerate(results[:max], start=1):
            segment = offer['itineraries'][0]['segments'][0]
            flight_number = segment['carrierCode'] + segment['number']
            dep_time = segment['departure']['at'].replace("T", " ")[:16]
            arr_time = segment['arrival']['at'].replace("T", " ")[:16]
            duration = segment['duration'].replace("PT", "").lower()
            price = offer['price']['total']
            

            output += (
                f"Option {i}:\n"
                f"  • Flight: {flight_number}\n"
                f"  • From: {originLocationCode} at {dep_time}\n"
                f"  • To: {destinationLocationCode} at {arr_time}\n"
                f"  • Duration: {duration}\n"
                f"  • Price: {currencyCode} {price}\n\n"
            )

        return output.strip(),results

    except ResponseError as e:
        return f"Amadeus API error: {str(e)}"
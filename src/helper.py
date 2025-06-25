from amadeus import Client, ResponseError
from typing import Optional, List
from agno.tools import tool
from src.instructions import FAQ_data
from dotenv import load_dotenv 
import os 
import re
import requests
load_dotenv()
amadeus_api_key= os.getenv("AMADEUS_API_KEY")
amadeus_api_secret = os.getenv("AMADEUS_API_SECRET")
BASE_URL = os.getenv("BASE_URL")
amadeus = Client(
    client_id = amadeus_api_key,
    client_secret = amadeus_api_secret
)
@tool
def search_flights(
    originLocationCode: str,
    destinationLocationCode: str,
    departureDate: str,
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
)-> dict:
    """
    Search for flights using the Amadeus API.
    Returns a list of flight options or a user-friendly error message.
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
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}

        response = amadeus.shopping.flight_offers_search.get(**params)
        results = response.data

        if not results:
            return {
                "type" : "search_flights",
                "success": True,
                "message": f"No flights found from {originLocationCode} to {destinationLocationCode} on {departureDate}.",
                "data":None
            }

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
                f"  • Price: {currencyCode or 'USD'} {price}\n\n"
            )

        return {
            "type" : "search_flights",
            "success": True,
            "message": output.strip(),
            "data": results  # optional: useful for internal follow-up lookups
        }

    except ResponseError as e:
        return {
            "type" : "search_flights",
            "success": False,
            "message": f"❌ Sorry, we're having trouble accessing flight data at the moment. Please try again later.",
            "data":None
        }

    except Exception as e:
        return {
            "type" : "search_flights",
            "success": False,
            "message": "❌ An unexpected error occurred while searching for flights. Please try again later.",
            "data":None
        }

    #---------------------------------------------------------------------
    ######################## Customer Support ############################
    #---------------------------------------------------------------------

@tool
def booked_flight(access_token: str) -> dict:
    """
    Fetches confirmed bookings for the authenticated user using the access token.
    
    Behavior:
    - If no confirmed bookings → inform the user.
    - If one confirmed booking → auto-cancel by returning its bookingRef.
    - If multiple → show the list and ask the user to pick a bookingRef.
    """
    if not access_token:
        return {
            "type" : "booked_flight",
            "success":True,
            "message": "You're not authenticated. Please log in first.",
            "data":None
        }

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = requests.get(f"{BASE_URL}/booking/my-bookings", headers=headers)
        response.raise_for_status()
        all_bookings = response.json().get("data", {}).get("bookings", [])
        confirmed = [b for b in all_bookings if b.get("status") == "confirmed"]

        if not confirmed:
            return {
                "type" : "booked_flight",
                "success" : True,
                "message": "You have no confirmed bookings to cancel.",
                "data":None
            }

        if len(confirmed) == 1:
            booking = confirmed[0]
            return {
                "type" : "booked_flight",
                "success":True,
                "message": f"Found one confirmed booking: {booking['originCity']} → {booking['destinationCity']} on {booking['departureDate'].split('T')[0]} with bookingRef { booking["bookingRef"]}.\nProceeding to cancel this booking.",
                "data":None
            }

        options = "\n".join([
            f"{i+1}. {b['originCity']} → {b['destinationCity']} on {b['departureDate'].split('T')[0]} | Ref: {b['bookingRef']}"
            for i, b in enumerate(confirmed)
        ])

        return {
            "type" : "booked_flight",
            "success": True,
            "message": f"Here are your confirmed bookings:\n\n{options}\n\nPlease provide the booking reference you'd like to cancel.",
            "data":None
        }

    except Exception as e:
        return {
            "type" : "booked_flight",
            "success" : False,
            "message": f"Failed to retrieve bookings. Please try again later.",
            "data":None
        }

@tool
def cancel_flight(access_token: str, bookingRef: str) -> dict:
    """
    Cancels the booking with the given bookingRef and the access token 
    make sure that the user should provide the bookingref.
    """
    if not access_token or not bookingRef:#here
        return {"type":"cancel_flight",
            "success": True,
            "message": "❌ Missing access token or booking reference.",
            "data":None}

    try:
        # Try to look up the booking using bookingRef to get the booking ID
        headers = {"Authorization": f"Bearer {access_token}"}
        booking_lookup = requests.get(
            f"{BASE_URL}/booking/my-bookings",
            headers=headers,
        )
        booking_lookup.raise_for_status()
        bookings = booking_lookup.json().get("data", {}).get("bookings", [])

        match = next((b for b in bookings if b["bookingRef"] == bookingRef), None)
        if not match:
            return {
                "type":"cancel_flight",
                "success":True,
                "message": "❌ Booking reference not found. Please try again.",
                "data":None}
    

        booking_id = match.get("_id")
        if not booking_id:
            return {
                "type":"cancel_flight",
                "success" :True,
                "message": "❌ Could not extract booking ID. Cannot proceed.",
                "data":None}

        # Proceed to cancel
        cancel_response = requests.post(
            f"{BASE_URL}/booking/{booking_id}/cancel",
            headers=headers,
        )
        cancel_response.raise_for_status()
        return {"type":"cancel_flight",
                "success" : True,
                "message": "✅ Your booking has been successfully cancelled.",
                "data":None}

    except Exception as e:
        return {"type":"cancel_flight",
                "success" : False,
                "message": f"❌ Something went wrong while cancelling.",
                "data":None}
# @tool
def update_user_profile(
    access_token: str,
    firstName: Optional[str] = None,
    lastName: Optional[str] = None,
    phoneNumber: Optional[str] = None,
    country: Optional[str] = None,
    birthdate: Optional[str] = None,
    gender: Optional[str] = None,
    preferredLanguage: Optional[str] = None,
    preferredAirlines: Optional[List[str]] = None,
    deviceType: Optional[str] = None,
    preferredCabinClass: Optional[str] = None,
    useRecommendationSystem: Optional[bool] = None
) :#-> dict:
    """
    Updates user profile fields that users are allowed to change.
    Returns a friendly message for the chatbot, even on error.
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "firstName": firstName,
        "lastName": lastName,
        "phoneNumber": phoneNumber,
        "country": country,
        "birthdate": birthdate,
        "gender": gender,
        "preferredLanguage": preferredLanguage,
        "preferredAirlines": preferredAirlines,
        "deviceType": deviceType,
        "preferredCabinClass": preferredCabinClass,
        "useRecommendationSystem": useRecommendationSystem
    }

    # Clean out None values
    clean_payload = {k: v for k, v in payload.items() if v is not None}

    try:
        response = requests.patch(f"{BASE_URL}/users/profile", json=clean_payload, headers=headers)
        data = response.json()
        if response.status_code >= 400:
            return {
                "type":"update_user_profile",
                "success": False,
                "message": "⚠️ Couldn't update your profile. Please check your input and try again.",
                "data":None
            }

        return {
            "type":"update_user_profile",
            "success": True,
            "message": "✅ Your profile was updated successfully.",
            "data":None
        }

    except Exception:
        return {
            "type":"update_user_profile",
            "success": False,
            "message": "❌ Sorry, something went wrong while updating your profile. Please try again later.",
            "data":None
        }


def is_strong_password(pw: str) -> bool:
        return (
            len(pw) >= 10 and
            re.search(r"[A-Z]", pw) and
            re.search(r"[a-z]", pw) and
            re.search(r"[0-9]", pw) and
            re.search(r"[^A-Za-z0-9]", pw)
        )
@tool
def change_user_password(
    access_token: str,
    oldPassword: str,
    newPassword: str
)-> dict:
    """
    Change the user's password.

    Requires:
    - access_token: User's access token (from login)
    - oldPassword: The current password
    - newPassword: The new password to be set
    """
    if not is_strong_password(newPassword):
        return {
            "type":"change_user_password",
            "success": True,
            "message": "❌ New password is not strong enough. It must be at least 10 characters long and include an uppercase letter, lowercase letter, number, and symbol.",
            "data":None
        }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "oldPassword": oldPassword,
        "newPassword": newPassword
    }

    try:
        response = requests.put(f"{BASE_URL}/users/change-password", json=payload, headers=headers)
        data = response.json()

        if response.status_code >= 400:
            return {
                "type":"change_user_password",
                "success": False,
                "message": data.get("message", "⚠️ Failed to change password. Please make sure your old password is correct."),
                "data":None
            }

        return {
            "type":"change_user_password",
            "success": True,
            "message": "✅ Your password has been changed successfully.",
            "data":None
        }

    except Exception:
        return {
            "type":"change_user_password",
            "success": False,
            "message": "❌ Sorry, something went wrong while changing your password. Please try again later.",
            "data":None
        }

@tool 
def request_password_reset(email: str) -> dict:
    """
    Send a password reset code to the user's email.
    """
    payload = { "email": email }
    try:
        response = requests.post(f"{BASE_URL}/users/request-password-reset", json=payload)
        data = response.json()

        if response.status_code >= 400:
            return {
                "type":"request_password_reset",
                "success": False,
                "message": "⚠️ Failed to send reset code. Please make sure the email is correct.",
                "data":None
            }

        return {
            "type":"request_password_reset",
            "success": True,
            "message": "📧 A password reset code has been sent to your email.",
            "data":None
        }

    except Exception:
        return {
            "type":"request_password_reset",
            "success": False,
            "message": "❌ Something went wrong while requesting the password reset. Please try again later.",
            "data":None
        }

@tool
def reset_password_with_code(code: str, newPassword: str) -> dict:
    """
    Reset password using the verification code sent to the user's email.
    """
    # Validate password
    if not is_strong_password(newPassword):
        return {
            "type":"reset_password_with_code",
            "success": True,
            "message": "New password is not strong enough. It must be at least 10 characters long and include an uppercase letter, lowercase letter, number, and symbol.",
            "data":None
        }

    payload = {
        "code": code,
        "newPassword": newPassword
    }

    try:
        response = requests.post(f"{BASE_URL}/users/reset-password", json=payload)
        data = response.json()

        if response.status_code >= 400:
            return {
                "type":"reset_password_with_code",
                "success": False,
                "message": "❌ Failed to reset the password. Please check the code and try again.",
                "data":None
            }

        return {
            "type":"reset_password_with_code",
            "success": True,
            "message": "✅ Your password has been successfully reset. You can now log in with your new password.",
            "data":None
        }

    except Exception:
        return {
            "type":"reset_password_with_code",
            "success": False,
            "message": "❌ Something went wrong while resetting your password. Please try again later.",
            "data":None
        }
         #############################################################
         # --------------------Customer Service----------------------
         #############################################################
@tool
def customer_service(query: str) -> dict:
    """
    Handle common customer service queries and provide structured JSON responses.

    Args:
        query (str): The user's question or statement.

    Returns:
        dict: Structured JSON response.
    """
    try:
        normalized_query = query.lower()
        matched_airline = None

        # Airline keyword detection
        airline_keywords = {
            "emirates": "emirates",
            "qatar": "qatar airways",
            "qatar airways": "qatar airways",
            "saudi": "saudi airlines",
            "saudi airlines": "saudi airlines",
            "etihad": "etihad",
            "flydubai": "flydubai"
        }

        for key in airline_keywords:
            if key in normalized_query:
                matched_airline = airline_keywords[key]
                break

        # Smart intent recognition
        if any(word in normalized_query for word in ["laptop", "bag", "personal item", "carry-on", "cabin bag", "hand luggage"]):
            intent = "baggage policy"
        elif any(word in normalized_query for word in ["refund", "money back", "cancel my ticket"]):
            intent = "refund rules"
        elif any(word in normalized_query for word in ["reschedul", "change", "change my ticket", "change flight", "modify booking"]):
            intent = "rescheduling"
        elif any(word in normalized_query for word in ["excess", "extra weight", "too heavy", "overweight", "bag too heavy"]):
            intent = "excess baggage"
        elif any(word in normalized_query for word in ["visa", "travel document", "entry permit"]):
            intent = "visa requirements"
        elif any(word in normalized_query for word in ["check-in", "check in", "boarding pass", "when can I check"]):
            intent = "check-in policy"
        elif any(word in normalized_query for word in ["pet", "dog", "cat", "animal", "bring my pet"]):
            intent = "pet policy"
        elif any(word in normalized_query for word in ["meal", "food", "vegetarian", "special meal", "kosher", "halal"]):
            intent = "meal options"
        else:
            return {
                "type": "customer_service",
                "success": False,
                "message": "Sorry, I couldn’t find a clear answer to that. I can help you with baggage policies, check-in, refunds, ticket changes, and more — feel free to ask!",
                "data":None
            }

        faq_data = FAQ_data
        # Final response
        if matched_airline and matched_airline in faq_data[intent].get("specific", {}):
            reply = faq_data[intent]["specific"][matched_airline]
        else:
            reply = faq_data[intent].get("default", "Let me help you with that.")

        return {
            "type": "customer_service",
            "success": True,
            "message": reply,
            "data":None
        }

    except Exception as e:
        return {
            "type": "customer_service",
            "success": False,
            "message": "An error occurred while processing your request",
            "data":None
        }
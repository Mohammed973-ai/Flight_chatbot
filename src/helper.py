from amadeus import Client, ResponseError
from typing import Optional, List
from agno.tools import tool
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
def customer_service(query: str) -> str:
    """
    Handle common customer service queries and provide responses.
    """
    faq_responses = {
        "baggage policy": {
            "default": "Most airlines allow a carry-on bag and a personal item like a laptop bag. Would you like details for a specific airline?",
            "specific": {
                "emirates": "Emirates allows up to 7kg for carry-on in economy class.",
                "qatar airways": "Qatar Airways allows 7kg in economy class for carry-on.",
                "saudi airlines": "Saudi Airlines permits 7kg for carry-on baggage in economy.",
                "etihad": "Etihad permits 7kg for carry-on in economy class.",
                "flydubai": "Flydubai allows 7kg carry-on baggage in economy."
            }
        },
        "refund rules": {
            "default": "Refund rules depend on the airline and ticket type. Would you like help checking specific rules?",
            "specific": {
                "emirates": "Refunds for Emirates flights depend on the fare conditions of your ticket.",
                "qatar airways": "Qatar Airways offers refunds based on ticket type; check their website for details.",
                "saudi airlines": "Saudi Airlines allows refunds for refundable tickets with applicable charges.",
                "etihad": "Etihad processes refunds based on fare rules and ticket conditions.",
                "flydubai": "Flydubai provides refunds only for refundable tickets, with certain fees applied."
            }
        },
        "rescheduling": {
            "default": "You can reschedule your flight through the airline's website or customer service. Need help with a specific airline?",
            "specific": {
                "emirates": "Emirates allows rescheduling for most tickets via their website or app.",
                "qatar airways": "Qatar Airways permits changes to tickets based on fare conditions.",
                "saudi airlines": "Saudi Airlines allows flight changes online or via customer service.",
                "etihad": "Etihad allows rescheduling based on ticket type; fees may apply.",
                "flydubai": "Flydubai permits rescheduling online for refundable tickets with applicable fees."
            }
        },
        "excess baggage": {
            "default": "If your baggage exceeds the weight limit, extra charges may apply. Would you like details for a specific airline?",
            "specific": {
                "emirates": "Excess baggage fees for Emirates start at $15 per kg depending on the route.",
                "qatar airways": "Qatar Airways charges excess baggage fees starting at $25 per kg based on the route.",
                "saudi airlines": "Saudi Airlines applies a charge of $20 per kg for excess baggage.",
                "etihad": "Etihad charges for excess baggage depend on the route and start at $25 per kg.",
                "flydubai": "Flydubai charges excess baggage fees based on the route, starting at $10 per kg."
            }
        },
        "visa requirements": {
            "default": "Visa requirements depend on your destination and nationality. Would you like me to check for a specific country?",
            "specific": {
                "emirates": "Emirates provides a visa service for UAE entry; check their website for eligibility.",
                "qatar airways": "Qatar Airways offers transit visas for eligible passengers traveling via Doha.",
                "saudi airlines": "Saudi Airlines offers Umrah and tourist visa assistance on their website.",
                "etihad": "Etihad assists with UAE tourist visas for eligible passengers; check their website.",
                "flydubai": "Flydubai provides a visa application service for UAE visitors."
            }
        },
        "check-in policy": {
            "default": "Most airlines allow check-in 24-48 hours before departure. Want help checking the policy for your flight?",
            "specific": {
                "emirates": "Emirates opens online check-in 48 hours before flight departure.",
                "qatar airways": "Qatar Airways allows online check-in starting 48 hours before departure.",
                "saudi airlines": "Saudi Airlines opens check-in 24 hours before flight departure.",
                "etihad": "Etihad permits online check-in 30 hours before flight departure.",
                "flydubai": "Flydubai offers online check-in starting 48 hours before departure."
            }
        },
        "pet policy": {
            "default": "Many airlines allow pets onboard under certain conditions. Want me to check a specific airline's policy?",
            "specific": {
                "emirates": "Emirates allows pets as checked baggage or cargo; restrictions apply.",
                "qatar airways": "Qatar Airways permits pets in the cargo hold only.",
                "saudi airlines": "Saudi Airlines allows pets as cargo; contact customer service for details.",
                "etihad": "Etihad accepts pets in the cargo hold for international flights.",
                "flydubai": "Flydubai permits pets as cargo; advance booking is required."
            }
        },
        "meal options": {
            "default": "Meal options vary by airline and route. Would you like details for your flight?",
            "specific": {
                "emirates": "Emirates offers special meals like vegetarian, diabetic, and gluten-free meals.",
                "qatar airways": "Qatar Airways provides a variety of special meals upon request.",
                "saudi airlines": "Saudi Airlines offers special meal options for dietary preferences.",
                "etihad": "Etihad provides customizable meal options, including vegetarian and kosher meals.",
                "flydubai": "Flydubai offers pre-order meal options for most routes."
            }
        }
    }

    normalized_query = query.lower()

    for category, responses in faq_responses.items():
        if category in normalized_query:
            if "specific" in responses:
                for airline, detail in responses["specific"].items():
                    if airline in normalized_query:
                        return detail
            return responses["default"]

    return (
        "I'm sorry, I couldn't find an answer to your question. "
        "Would you like me to escalate this to a human agent?"
    )

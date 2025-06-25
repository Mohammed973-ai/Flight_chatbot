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

    Args:
        query (str): The user's question or statement.

    Returns:
        str: Chatbot's response.
    """
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
        return "Sorry, I couldn’t find a clear answer to that. I can help you with baggage policies, check-in, refunds, ticket changes, and more — feel free to ask!"

    # FAQ data
    faq_data = {
    "baggage policy": {
        "default": (
            "Most airlines allow passengers to bring a carry-on bag (typically up to 7kg) "
            "and one personal item such as a laptop bag or handbag in economy class. "
            "Weight and size limits may vary between airlines. "
            "Would you like details for a specific airline like Emirates, Qatar Airways, or Flydubai?"
        ),
        "specific": {
            "emirates": "Emirates allows up to 7kg of carry-on baggage in economy class. Passengers may also bring one personal item such as a laptop bag. Size limits apply (55 x 38 x 20 cm). Additional allowances are available for premium classes. More info: https://www.emirates.com/english/help/faq-topics/baggage/",
            "qatar airways": "Qatar Airways permits one piece of carry-on baggage up to 7kg in economy class. In addition, passengers can carry one small personal item. Business and First Class allow more weight and pieces. More info: https://www.qatarairways.com/en/baggage/allowance.html",
            "saudi airlines": "Saudi Airlines allows one carry-on item weighing up to 7kg for economy class passengers, plus a personal item such as a small handbag or laptop case. More info: https://www.saudia.com/en/plan-and-book/travel-information/baggage-information",
            "etihad": "Etihad permits economy class passengers to bring a carry-on bag up to 7kg and a small personal item. Dimensions should not exceed 56 x 36 x 23 cm. More info: https://www.etihad.com/en/help/baggage",
            "flydubai": "Flydubai allows passengers in economy class to carry one bag up to 7kg and one small personal item. Oversized or overweight items may incur fees. More info: https://www.flydubai.com/en/plan/baggage"
        }
    },
    "refund rules": {
        "default": (
            "Refund eligibility depends on the airline and the ticket type you purchased. "
            "Some tickets are fully refundable, others are partially refundable with penalties, "
            "and some may be non-refundable. Refunds are typically processed through the original payment method. "
            "Would you like help checking a specific airline's policy?"
        ),
        "specific": {
            "emirates": "Emirates allows ticket refunds depending on the fare conditions. Refundable tickets can be canceled online, while non-refundable tickets may still offer partial refunds or travel vouchers in some cases. More info: https://www.emirates.com/english/help/faq-topics/tickets/refunds/",
            "qatar airways": "Qatar Airways processes refunds based on fare type. Refundable tickets are fully refundable minus any service fees. Non-refundable fares may be eligible for credit vouchers. More info: https://www.qatarairways.com/en/help/refund-request.html",
            "saudi airlines": "Saudi Airlines offers full or partial refunds depending on ticket class. Refunds may incur service fees. Cancellations can be requested online or via customer service. More info: https://www.saudia.com/en/manage-my-booking/refund",
            "etihad": "Etihad refunds depend on ticket flexibility. Fully flexible tickets are refundable without a penalty, while promotional fares may not be refundable. Refunds are processed to the original form of payment. More info: https://www.etihad.com/en/manage/refund",
            "flydubai": "Flydubai provides refunds only for refundable tickets. Non-refundable tickets are not eligible for money back, but passengers might get credit in some scenarios. Service charges may apply. More info: https://www.flydubai.com/en/plan/ticket-options"
        }
    },
    "rescheduling": {
        "default": (
            "You can usually change your flight through the airline's website, mobile app, or by contacting customer service. "
            "Most airlines allow changes with possible fees depending on your ticket class and conditions. "
            "Some tickets might not be eligible for changes. "
            "Would you like me to check the rules for a specific airline like Emirates, Qatar Airways, or Flydubai?"
        ),
        "specific": {
            "emirates": "Emirates allows most tickets to be changed online or through their contact centers. Change fees depend on ticket fare conditions. Some promotional fares may have restrictions. More info: https://www.emirates.com/english/help/faq-topics/tickets/changes/",
            "qatar airways": "Qatar Airways lets you modify your booking through their website or app. Fees depend on fare type. During certain promotions or crises, free changes may apply. More info: https://www.qatarairways.com/en/help/faq/booking-modification.html",
            "saudi airlines": "Saudi Airlines permits ticket rescheduling online or by calling support. Changes are subject to availability and fare rules, with possible penalties or fare differences. More info: https://www.saudia.com/en/manage-my-booking/change-flight",
            "etihad": "Etihad allows rescheduling based on ticket type. Economy Saver fares may have limited flexibility, while Economy Flex and higher classes allow easier changes with lower or no fees. More info: https://www.etihad.com/en/manage/change-booking",
            "flydubai": "Flydubai allows flight changes via their website. Refundable tickets can be changed with minimal fees, while non-refundable tickets may not allow changes. Fare differences apply. More info: https://www.flydubai.com/en/plan/ticket-options"
        }
    },
    "excess baggage": {
        "default": (
            "If your baggage exceeds the weight limit, most airlines will charge an excess baggage fee. "
            "These fees vary depending on the airline, route, and class of travel. "
            "Typically, fees are charged per extra kilogram or as a flat rate. "
            "Would you like to know the rates for a specific airline?"
        ),
        "specific": {
            "emirates": "Excess baggage with Emirates can cost from $15 to $50 per kg depending on route. Pre-paying online is usually cheaper than paying at the airport. More info: https://www.emirates.com/english/help/faq-topics/baggage/excess-baggage/",
            "qatar airways": "Qatar Airways charges from $25 per kg on most routes. Rates can vary by region and booking method. Prepaid excess baggage discounts may apply. More info: https://www.qatarairways.com/en/baggage/excess.html",
            "saudi airlines": "Saudi Airlines charges about $20 per kg for extra baggage. Discounts are sometimes offered for advance online payment. More info: https://www.saudia.com/en/plan-and-book/travel-information/baggage-information/excess-baggage",
            "etihad": "Etihad’s excess baggage fees start at around $25 per kg, varying by route. They also offer prepaid baggage bundles. More info: https://www.etihad.com/en/help/baggage",
            "flydubai": "Flydubai has route-based pricing starting at $10 per kg for excess baggage. Prepaid options are more economical. More info: https://www.flydubai.com/en/plan/baggage"
        }
    },
    "visa requirements": {
        "default": (
            "Visa requirements vary depending on your destination, nationality, and purpose of travel. "
            "Some airlines offer visa assistance services or transit visas. "
            "Would you like help checking the requirements for a specific airline or country?"
        ),
        "specific": {
            "emirates": "Emirates offers visa services for UAE travel, including tourist and transit visas. Applications can be submitted online if your ticket is booked through Emirates. More info: https://www.emirates.com/english/before-you-fly/visa-passport-information/uae-visa-information/",
            "qatar airways": "Qatar Airways provides assistance for transit visas through Doha for eligible passengers. They also help with tourist visa applications when entering Qatar. More info: https://www.qatarairways.com/en/visa.html",
            "saudi airlines": "Saudi Airlines facilitates visa applications for Umrah, Hajj, and general tourism through their platform. They also support eVisa processes. More info: https://www.saudia.com/en/plan-and-book/travel-information/visa-information",
            "etihad": "Etihad helps with UAE visa applications for ticket holders. Services include 96-hour transit visas, short-term, and long-term tourist visas. More info: https://www.etihad.com/en/before-you-fly/visas",
            "flydubai": "Flydubai provides UAE visa application assistance for tourists. You can apply online if you’ve booked your flight with them. More info: https://www.flydubai.com/en/flying-with-us/visas"
        }
    },
    "check-in policy": {
        "default": (
            "Most airlines allow online check-in 24–48 hours before departure. "
            "You can also check in at the airport counters, though online check-in is recommended for faster processing. "
            "Would you like to check the timing for a specific airline?"
        ),
        "specific": {
            "emirates": "Emirates allows online check-in starting 48 hours and up to 90 minutes before departure. Baggage drop closes 60 minutes before takeoff. More info: https://www.emirates.com/english/manage-booking/online-check-in/",
            "qatar airways": "Online check-in with Qatar Airways starts 48 hours and closes 90 minutes before flight. Airport check-in usually opens 3 hours before. More info: https://www.qatarairways.com/en/manage-booking/check-in.html",
            "saudi airlines": "Saudi Airlines check-in opens 24 hours before departure online, and airport counters open 3 hours prior to international flights. More info: https://www.saudia.com/en/manage-my-booking/check-in",
            "etihad": "Etihad check-in starts online 30 hours before departure. Airport counters typically open 3–4 hours before takeoff. More info: https://www.etihad.com/en/manage/check-in",
            "flydubai": "Flydubai offers online check-in from 48 hours to 75 minutes before flight time. Airport check-in opens 3 hours before departure. More info: https://www.flydubai.com/en/manage/check-in"
        }
    },
    "pet policy": {
        "default": (
            "Many airlines allow pets to travel either in the cabin (for small animals) or as checked baggage or cargo. "
            "Policies vary by airline, and advance booking is often required. "
            "Would you like to check the pet policy of a specific airline?"
        ),
        "specific": {
            "emirates": "Emirates allows pets to travel as checked baggage or cargo, depending on size and destination. Cabin travel for pets is generally not allowed, except for falcons on select routes. More info: https://www.emirates.com/english/help/faq-topics/baggage/pets/",
            "qatar airways": "Pets are allowed in the cargo hold only on Qatar Airways. Advance arrangements and health documentation are required. More info: https://www.qatarairways.com/en/baggage/animals.html",
            "saudi airlines": "Saudi Airlines accepts pets as cargo. Prior approval and vaccination records are required. Service animals have separate rules. More info: https://www.saudia.com/en/fly-with-us/travel-information/traveling-with-pets",
            "etihad": "Etihad permits pets in the cargo hold. Small service animals may travel in the cabin under certain rules. More info: https://www.etihad.com/en/fly-etihad/travel-extra/pets",
            "flydubai": "Flydubai allows pets to travel as manifest cargo. Cabin travel is not allowed. Booking should be completed in advance. More info: https://www.flydubai.com/en/flying-with-us/travelling-with-pets"
        }
    },
    "meal options": {
        "default": (
            "Most airlines provide complimentary meals on international flights, and many offer special meals upon request "
            "(e.g., vegetarian, diabetic, halal, kosher). Some low-cost carriers may require pre-ordering. "
            "Would you like to check the options available with a specific airline?"
        ),
        "specific": {
            "emirates": "Emirates offers complimentary gourmet meals and a wide range of special meals (vegetarian, vegan, halal, gluten-free, etc.). Special meal requests should be made at least 24 hours in advance. More info: https://www.emirates.com/english/experience/dining/",
            "qatar airways": "Qatar Airways serves high-quality meals and over 20 special meal options for various dietary and religious needs. Requests should be made during booking or later via Manage Booking. More info: https://www.qatarairways.com/en/onboard/dining.html",
            "saudi airlines": "Saudi Airlines provides halal meals by default and offers special meal options for diabetic, vegetarian, and children’s meals. Requests must be made before the flight. More info: https://www.saudia.com/en/fly-with-us/travel-information/special-meals",
            "etihad": "Etihad provides a range of complimentary meals in all classes. Passengers can pre-order special meals like vegetarian, kosher, or gluten-free from a list of over 15 types. More info: https://www.etihad.com/en/fly-etihad/onboard/dining",
            "flydubai": "Flydubai offers pre-order meal services with choices like sandwiches, snacks, and hot meals. Special dietary options are available depending on the route. More info: https://www.flydubai.com/en/flying-with-us/meal-options"
        }
    }
}
    # Final response
    if matched_airline and matched_airline in faq_data[intent].get("specific", {}):
        return faq_data[intent]["specific"][matched_airline]
    else:
        return faq_data[intent].get("default", "Let me help you with that.")

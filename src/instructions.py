Instructions = ["""
✈️ You are a helpful and professional flight assistant in a flight platform.
You will be communicating with frontend and backend so PLEASE I need formatted JSON like this:               
{
  "type": "search_flights" | "booked_flight" | "cancel_flight" | "change_user_password" | "update_user_profile"
           "request_password_reset" | "reset_password_with_code" | "no_tool_call"|"customer_service",
  "success": true | false(in case of exception),
  "message": "type your reply to the user here",
    "login" :True (in case the tool you use need an access token and it is not provided) |False (in case the access token is provided or the tool doesnt need access_token) 
  "data":  # ONLY include 'data' when using the 'search_flights' tool and it should include the response of the flights of  amadus flights api you will find this returned in the tool in the "data" or **null**
}

❗ DONT TYPE ANY INTRODUCTORY SENTENCES.
🗣️ IF YOU WANT TO TALK OR CHAT WITH THE USER, YOU MUST PUT IT INSIDE THE "message" FIELD IN THE JSON RESPONSE.

CALL tools when needed and execute them. DO NOT LIE TO THE USER.
You are responsible for handling ONLY the tasks described below.

---

🔧 **Available Tools & Usage**

1. **search_flights**Dont forget to call and execute the tool
   - Description: Searches available flights using the Amadeus API.
   - Required Inputs: `originLocationCode`, `destinationLocationCode`, `departureDate`
   - Returns: A clearly formatted response in the "message" and  the api json response from amadeus in the "data" if doesnt exist put null .
                
2. **booked_flight**Dont forget to call and execute the tool

   - Description: Retrieves the user’s confirmed bookings.
   - Input: `access_token`
   - Output: 
     - If 1 booking → auto-cancel it using `cancel_flight`.
     - If multiple → list them and wait for user to choose `bookingRef`.
     - If none → inform user politely.

3. **cancel_flight**Dont forget to call and execute the tool

   - Description: Cancels a selected booking.
   - Inputs: `access_token`, `bookingRef`
   - Output: Confirmation message of cancellation.

4. **change_user_password**Dont forget to call and execute the tool

   - Description: Changes the user’s password.
   - Inputs: `access_token`, `oldPassword`, `newPassword`
   - Output: Confirmation or error message.

5. **request_password_reset**Dont forget to call and execute the tool

   - Description: Sends a reset code to the user’s email.
   - Input: `email`
   - Output: Message indicating success or failure.

6. **reset_password_with_code**Dont forget to call and execute the tool

   - Description: Resets password using a code.
   - Inputs: `code`, `newPassword`
   - Output: Message confirming success or failure.

7. **customer_service**Dont forget to call and execute the tool

   - Description: Answers common flight-related service questions.
   - Input: `query` (user’s full question)
   - Output: Response about:
     - baggage policy
     - refund rules
     - rescheduling
     - excess baggage
     - visa requirements
     - check-in policy
     - pet policy
     - meal options
   - Format: 
     {
       "type": "no_tool_call",
       "success": true,
       "message": "Qatar Airways allows 7kg in economy class for carry-on."
     }
   - If no match found:
     {
       "type": "no_tool_call",
       "success": true,
       "message": "I'm sorry, I couldn't find an answer to your question. Would you like me to escalate this to a human agent?"
     }
8. **update user profile**Dont forget to call and execute the tool
   - Description: Updates user profile fields that users are allowed to change. 
   - Inputs: access_token: str,
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
   - Output: Message confirming success or failure.
---

🔒 **General Rules**

❌ If user asks something outside your scope (e.g., hotels, jokes, weather):
> Respond with: "I'm here to help only with flight search and cancellation. Let me know if you'd like help with either!"

✅ Always respond with clarity and professionalism.
✅ Keep JSON response clean, correct, and only in the specified format.

---

🔍 **Flight Search Workflow**

1. Always use `search_flights` tool for flight questions — never guess.
2. User must provide: origin, destination, and departure date.
3. If any required field is missing, ask politely for it.
4. Do not ask for optional filters unless user gives them.
5. Format results in message and put the full flight list in `"data"` field.

---

🧾 **Flight Cancellation Workflow**

1. Use `booked_flight` first with `access_token`.
2. If:
   - One booking → call `cancel_flight` directly.
   - Multiple → list bookings and wait for user's `bookingRef`.
   - None → reply politely.
3. Use `cancel_flight` with selected `bookingRef`.
4. Handle bad references or errors politely.

---

⛔ DO NOT request the same data twice if it already exists in session.
"""]

FAQ_data = {
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

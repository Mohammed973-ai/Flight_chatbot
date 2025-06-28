# ✈️ Flight Chatbot API

This API allows users to interact with a smart flight chatbot for operations like searching flights, booking, canceling, updating profiles, changing passwords, and more.

---

## 📍 Base URL

> **Note:** The base URL is not yet determined.

---

## 🔁 Method

**POST** `/chat`

---

## 📥 Input JSON

Send a POST request with the following JSON body:

```json
{
  "message": "I want to change my password from .. to ..",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2ODU1YTJhMjMwYjhiMzA..",
  "user_id": "1",
  "session_id": "2"
}
```

- **message** : the user's message
- **access_token**: optional field
- **user_id** : can be any string like "1" or "u1"
- **session_id**: can be any string like "2" or "sess2"

## 📥 Output JSON

```json
{
  "response": {
    "type": "change_user_password",
    "success": true,
    "message": "Your password has been updated successfully.",
    "login": false,
    "data": null
  }
}
```

**type** : tells you what the chatbot did whether it used a tool or ran into error and all posible values are ["error","json_error","search_flights", "booked_flight","cancel_flight" ,"update_user_profile","change_user_password", "request_password_reset", "reset_password_with_code", "customer_service", "no_tool_call"]

- **success** : False in case of exception occurred
- **message** : chatbot reply
- **login** : True , if user not logged in and want to use a service that need them to login, False in case the user logged in or the tool doesnt need them to login
- **data** : contains response of flight searches or null

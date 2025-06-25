from src.chatbot import agent,memory
# Testing the Agent
session_id = "session_1"
user_id = "user_1"

test_cases = [
    # === DEFAULTS (1 per intent) ===
    "Can I carry a laptop bag in cabin?",                     # baggage policy
    "Can I get my money back if I cancel my flight?",     # refund rules
    "Is it possible to change my ticket?",                # rescheduling
    "What if my bag is overweight?",                      # excess baggage
    "Do I need a visa for travel?",                       # visa requirements
    "When can I check in for my flight?",                 # check-in policy
    "Can I bring my dog on the flight?",                  # pet policy
    "Do airlines serve halal meals?",                     # meal options

    # === SPECIFICS (8 intents × 5 airlines) ===
    # Baggage Policy
    "What is the baggage allowance on Emirates?",
    "Tell me about carry-on limits for Qatar Airways.",
    "How much hand luggage can I take with Saudi Airlines?",
    "Etihad cabin baggage rules?",
    "Flydubai carry-on weight limit?",

    # Refund Rules
    "Can I get a refund on Emirates?",
    "What’s the refund policy for Qatar Airways?",
    "Does Saudi Airlines allow ticket refunds?",
    "Etihad refund process?",
    "Flydubai refund conditions?",

    # Rescheduling
    "Can I change my booking on Emirates?",
    "How do I reschedule with Qatar Airways?",
    "Change my flight on Saudi Airlines?",
    "Etihad flight change policy?",
    "Can I modify my ticket with Flydubai?",

    # Excess Baggage
    "Extra baggage fees on Emirates?",
    "Qatar Airways overweight baggage charges?",
    "How much does Saudi Airlines charge for extra bags?",
    "Etihad excess weight policy?",
    "Flydubai baggage overweight fees?",

    # Visa Requirements
    "Does Emirates help with UAE visa?",
    "Qatar Airways transit visa information?",
    "Saudi Airlines visa assistance for Umrah?",
    "Visa help by Etihad?",
    "Can Flydubai arrange a UAE tourist visa?",

    # Check-In Policy
    "When can I check in online with Emirates?",
    "Qatar Airways online check-in timing?",
    "Saudi Airlines check-in start time?",
    "How early can I check in with Etihad?",
    "Flydubai check-in time window?",

    # Pet Policy
    "Can I bring a pet with Emirates?",
    "Qatar Airways pet travel policy?",
    "Does Saudi Airlines allow pets?",
    "Etihad policy on traveling with animals?",
    "How to transport a cat with Flydubai?",

    # Meal Options
    "What meals does Emirates serve onboard?",
    "Qatar Airways vegetarian meals?",
    "Meal service on Saudi Airlines?",
    "Etihad onboard dining options?",
    "Does Flydubai have special meals?",

    # === INVALID ===
    "alksdjalksdjflkasdjf"
]

for i, query in enumerate(test_cases, 1):
    print(f"\n--- Test Case {i} ---")
    print(f"User: {query}")

    # Clear memory before each test (simulate fresh session)
    memory.clear()

    # Run chatbot response
    print(
        agent.print_response(
            query,
            session_id=session_id,
            user_id=user_id
        )
    )
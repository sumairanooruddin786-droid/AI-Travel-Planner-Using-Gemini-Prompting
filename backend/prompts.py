"""
prompts.py
----------
This module contains the three prompt-construction strategies required by the
assignment:

    1. Zero-Shot Prompting
    2. Few-Shot Prompting
    3. Structured Reasoning Prompting

Each function takes the same `TripRequest`-shaped dict and returns a single
prompt string that will be sent to the Gemini API. Keeping every prompt in one
place (instead of scattering strings through the API routes) makes it easy to
compare the three techniques side by side, which is the whole point of the
assignment.
"""

from typing import Dict, List


def _format_common_intro(data: Dict) -> str:
    """Shared block describing the traveler. Used by all three techniques so
    that the only real variable between techniques is *how* Gemini is asked
    to reason, not *what* it is told about the trip."""
    interests = ", ".join(data["interests"]) if data["interests"] else "no particular interests specified"
    return (
        f"Traveler name: {data['name']}\n"
        f"Destination: {data['destination']}\n"
        f"Trip length: {data['days']} day(s)\n"
        f"Total budget: ${data['budget']} (covers the whole trip, all travelers included)\n"
        f"Interests: {interests}\n"
        f"Travel style: {data['travel_style']}\n"
    )


OUTPUT_FORMAT_INSTRUCTIONS = (
    "Format your entire response in clean Markdown using exactly this structure:\n\n"
    "## Trip Overview\n"
    "A short 2-3 sentence summary of the plan and how it fits the traveler.\n\n"
    "## Day-by-Day Itinerary\n"
    "For each day, use a heading '### Day N: <short theme>' followed by "
    "'- **Morning:**', '- **Afternoon:**', '- **Evening:**' bullet points. "
    "Each bullet should name a specific place/activity and an estimated cost in USD.\n\n"
    "## Budget Summary\n"
    "A short bullet list breaking the estimated spend into categories "
    "(e.g. Lodging, Food, Activities, Transport) that add up to roughly the given budget.\n\n"
    "## Final Tip\n"
    "One practical closing tip for this specific traveler.\n\n"
    "Do not add any text before '## Trip Overview' or after the final tip."
)


def build_zero_shot_prompt(data: Dict) -> str:
    """
    PART 1: Zero-Shot Prompting.

    No examples are given. Gemini receives only a plain instruction and the
    traveler's raw preferences, and must figure out on its own how to
    analyze preferences, pick places, and build a day-by-day plan.
    """
    prompt = (
        "You are a professional travel planning assistant.\n\n"
        "Without referring to any prior examples, analyze the traveler's preferences below, "
        "suggest suitable places to visit, create a day-by-day itinerary, and recommend "
        "activities that fit within the stated budget.\n\n"
        f"{_format_common_intro(data)}\n"
        f"{OUTPUT_FORMAT_INSTRUCTIONS}"
    )
    return prompt


# ---------------------------------------------------------------------------
# PART 2: Few-Shot Prompting
# ---------------------------------------------------------------------------
# Three short worked examples covering different travel styles/budgets/
# interests, so Gemini has a concrete pattern to imitate before it sees the
# real traveler's details.
_FEW_SHOT_EXAMPLES: List[str] = [
    (
        "Example Traveler 1\n"
        "Name: Sara | Destination: Bangkok | Days: 3 | Budget: $450 | "
        "Interests: Food, Shopping | Travel Style: Solo\n"
        "Sample Plan:\n"
        "## Trip Overview\n"
        "A budget-friendly solo food-and-shopping crawl through Bangkok's street markets and malls.\n"
        "## Day-by-Day Itinerary\n"
        "### Day 1: Street Food Introduction\n"
        "- **Morning:** Chatuchak Weekend Market browsing ($5 entry, free)\n"
        "- **Afternoon:** Street food tour in Yaowarat/Chinatown ($15)\n"
        "- **Evening:** Rooftop bar with skyline view ($20)\n"
        "### Day 2: Markets and Malls\n"
        "- **Morning:** MBK Center shopping ($30 budget)\n"
        "- **Afternoon:** Siam Paragon window shopping + food court lunch ($15)\n"
        "- **Evening:** Asiatique The Riverfront night market ($25)\n"
        "### Day 3: Local Flavor\n"
        "- **Morning:** Cooking class with market visit ($35)\n"
        "- **Afternoon:** Relax at a local cafe, pack souvenirs ($10)\n"
        "- **Evening:** Farewell dinner at a night food street ($20)\n"
        "## Budget Summary\n"
        "- Food: $110\n- Shopping: $150\n- Activities: $60\n- Transport (BTS/tuk-tuk): $40\n"
        "## Final Tip\n"
        "Carry small bills - most street stalls and markets don't take cards.\n"
    ),
    (
        "Example Traveler 2\n"
        "Name: The Ahmed Family | Destination: Istanbul | Days: 5 | Budget: $1500 | "
        "Interests: History, Food | Travel Style: Family\n"
        "Sample Plan:\n"
        "## Trip Overview\n"
        "A family-paced Istanbul trip mixing historic sites with kid-friendly food stops.\n"
        "## Day-by-Day Itinerary\n"
        "### Day 1: Sultanahmet Highlights\n"
        "- **Morning:** Hagia Sophia and Blue Mosque ($20 combined)\n"
        "- **Afternoon:** Topkapi Palace, family ticket ($45)\n"
        "- **Evening:** Family dinner near Sultanahmet Square ($40)\n"
        "### Day 2: Bazaars and Bosphorus\n"
        "- **Morning:** Grand Bazaar browsing ($30 souvenirs)\n"
        "- **Afternoon:** Bosphorus family boat cruise ($60)\n"
        "- **Evening:** Casual seafood dinner in Karakoy ($55)\n"
        "(remaining days follow the same morning/afternoon/evening pattern)\n"
        "## Budget Summary\n"
        "- Lodging: $600\n- Food: $400\n- Activities: $350\n- Transport: $150\n"
        "## Final Tip\n"
        "Buy the Istanbul Museum Pass to skip lines at major historic sites as a family.\n"
    ),
    (
        "Example Traveler 3\n"
        "Name: Jordan | Destination: Costa Rica | Days: 6 | Budget: $1200 | "
        "Interests: Adventure, Nature | Travel Style: Friends\n"
        "Sample Plan:\n"
        "## Trip Overview\n"
        "An adventure-heavy group trip through Costa Rica's rainforests and volcanoes.\n"
        "## Day-by-Day Itinerary\n"
        "### Day 1: Arrival in La Fortuna\n"
        "- **Morning:** Arrive, check into hostel ($20/person)\n"
        "- **Afternoon:** Arenal Volcano hike ($40)\n"
        "- **Evening:** Group dinner, local soda ($15)\n"
        "### Day 2: Adrenaline Day\n"
        "- **Morning:** Zip-lining canopy tour ($70)\n"
        "- **Afternoon:** Natural hot springs ($35)\n"
        "- **Evening:** Bonfire and stargazing (free)\n"
        "(remaining days follow the same morning/afternoon/evening pattern)\n"
        "## Budget Summary\n"
        "- Lodging: $300\n- Food: $250\n- Activities: $500\n- Transport: $150\n"
        "## Final Tip\n"
        "Book zip-lining and rafting a few days ahead - group slots fill up fast in high season.\n"
    ),
]


def build_few_shot_prompt(data: Dict) -> str:
    """
    PART 2: Few-Shot Prompting.

    Shows Gemini 2-3 worked examples (different destinations, budgets,
    interests, travel styles) and then asks it to produce a new plan for the
    real traveler, following the same structure and level of detail.
    """
    examples_block = "\n\n".join(_FEW_SHOT_EXAMPLES)
    prompt = (
        "You are a professional travel planning assistant. Study the example travelers "
        "and their sample plans below, then create a new plan for the traveler at the end "
        "that matches the same style, structure, and level of detail.\n\n"
        f"{examples_block}\n\n"
        "---\n"
        "Now create a personalized plan for this new traveler:\n\n"
        f"{_format_common_intro(data)}\n"
        f"{OUTPUT_FORMAT_INSTRUCTIONS}"
    )
    return prompt


def build_structured_reasoning_prompt(data: Dict) -> str:
    """
    PART 3: Structured Reasoning Prompting.

    Gemini is walked through six explicit analysis steps, but is explicitly
    told NOT to reveal its internal chain of thought - only to use those
    steps internally and then produce the final itinerary with brief,
    one-line justifications for each recommendation.
    """
    prompt = (
        "You are a professional travel planning assistant. Work through the following "
        "steps internally, in order, to design the best possible trip - but do NOT show "
        "your internal reasoning, step numbers, or working. Only use the steps to arrive "
        "at a high-quality final answer:\n\n"
        "1. Analyze the traveler's preferences.\n"
        "2. Consider the available budget.\n"
        "3. Consider the number of travel days.\n"
        "4. Select suitable attractions and activities.\n"
        "5. Create a day-by-day itinerary.\n"
        "6. Prepare a brief (one sentence) justification for why each day's main "
        "recommendation was selected.\n\n"
        f"{_format_common_intro(data)}\n"
        "Now output ONLY the final result - no visible reasoning steps, no headings like "
        "'Step 1', no chain-of-thought. Add a short '*Why:* ...' line after each day's "
        "bullets with the one-sentence justification for that day's main pick.\n\n"
        f"{OUTPUT_FORMAT_INSTRUCTIONS}"
    )
    return prompt


TECHNIQUE_BUILDERS = {
    "zero-shot": build_zero_shot_prompt,
    "few-shot": build_few_shot_prompt,
    "structured": build_structured_reasoning_prompt,
}

TECHNIQUE_LABELS = {
    "zero-shot": "Zero-Shot Prompting",
    "few-shot": "Few-Shot Prompting",
    "structured": "Structured Reasoning Prompting",
}

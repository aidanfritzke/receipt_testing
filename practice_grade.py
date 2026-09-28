"""Records which practice items you missed, after doing the printed slip.

Launched by grade.bat. Reads practice_state.json, shows what this morning's
slip asked, takes the numbers you got wrong, and moves every card through the
Leitner boxes: missed cards drop to box 1 (due tomorrow), correct ones move up
a box and are not asked again until that box's interval has passed.
"""

import datetime
import json
import pathlib

DECK_PATH = pathlib.Path(__file__).with_name("practice_deck.json")
STATE_PATH = pathlib.Path(__file__).with_name("practice_state.json")
LEITNER_INTERVALS = {1: 1, 2: 2, 3: 4, 4: 8, 5: 16}
MAX_BOX = max(LEITNER_INTERVALS)


def main():
    try:
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        deck = json.loads(DECK_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print(f"Cannot read practice files: {error}")
        return
    pending = state.get("pending") or []
    if not pending:
        print("Nothing to grade - no slip has been printed since the last grading.")
        return

    cards = {card["id"]: card for card in deck.get("spanish", []) + deck.get("gregg", [])}
    print(f"\nSlip printed {state.get('printed_on', '?')}:\n")
    for entry in pending:
        card = cards.get(entry["id"], {})
        print(f"  {entry['number']}. {card.get('prompt', entry['id'])}")
        print(f"     -> {card.get('answer', '?')}")

    numbers = {entry["number"] for entry in pending}
    print(f"\nWhich did you miss? Numbers separated by spaces, or Enter for none.")
    try:
        answer = input("missed: ").strip()
    except EOFError:
        answer = ""
    missed = {int(token) for token in answer.replace(",", " ").split() if token.isdigit()}
    unknown = missed - numbers
    if unknown:
        print(f"Ignoring numbers not on this slip: {' '.join(str(n) for n in sorted(unknown))}")
    missed &= numbers

    today = datetime.date.today()
    for entry in pending:
        item = state["items"].setdefault(entry["id"], {"box": 1, "seen": 0, "missed": 0})
        was_missed = entry["number"] in missed
        item["box"] = 1 if was_missed else min(item.get("box", 1) + 1, MAX_BOX)
        item["seen"] = item.get("seen", 0) + 1
        item["missed"] = item.get("missed", 0) + (1 if was_missed else 0)
        item["due"] = (today + datetime.timedelta(days=LEITNER_INTERVALS[item["box"]])).isoformat()

    state["pending"] = []
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=1) + "\n",
                          encoding="utf-8")

    correct = len(pending) - len(missed)
    boxes = {}
    for item in state["items"].values():
        boxes[item.get("box", 1)] = boxes.get(item.get("box", 1), 0) + 1
    print(f"\nRecorded: {correct} of {len(pending)} correct.")
    print("Cards per box: "
          + ", ".join(f"box {box}: {boxes[box]}" for box in sorted(boxes)))
    print(f"Tracking {len(state['items'])} cards total.")


if __name__ == "__main__":
    main()

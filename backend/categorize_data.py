import json


def categorize_flashcards(flashcards):
    """Categorize flashcards based on performance."""
    categories = {
        "Mastered": [],
        "Correct but Needs Practice": [],
        "Needs More Work": [],
    }
    for flashcard in flashcards:
        status = flashcard.current_status()
        if status == "Mastered":
            categories["Mastered"].append(flashcard.to_dict())
        elif status == "Correct":
            categories["Correct but Needs Practice"].append(flashcard.to_dict())
        else:
            categories["Needs More Work"].append(flashcard.to_dict())
    return categories


def save_categorized_flashcards_to_json(
    categories, filepath="categorized_flashcards.json"
):
    """Save categorized flashcards to a JSON file."""
    with open(filepath, "w") as file:
        json.dump(categories, file, indent=4)
    print(f"Categorized flashcards saved to {filepath}")


def load_flashcards_from_category(filepath, category):
    """Load flashcards from a specific category."""
    try:
        with open(filepath, "r") as file:
            categories = json.load(file)
            if category in categories:
                return [flashcard for flashcard in categories[category]]
            else:
                print(f"No flashcards found in category: {category}")
                return []
    except FileNotFoundError:
        print("Categorized flashcards file not found.")
        return []

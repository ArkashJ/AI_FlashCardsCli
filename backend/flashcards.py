import json
import random
import time

import questionary
import torch
from sentence_transformers import SentenceTransformer, util
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class Flashcard:
    def __init__(self, question, answer, category, performance=None):
        self.question = question
        self.answer = answer
        self.category = category
        self.performance = performance if performance is not None else []

    def to_dict(self):
        return {
            "question": self.question,
            "answer": self.answer,
            "category": self.category,
            "performance": self.performance,
        }

    @staticmethod
    def from_dict(data):
        return Flashcard(
            data["question"], data["answer"], data["category"], data["performance"]
        )

    def update_performance(self, correct):
        """Updates the performance list based on the answer's correctness."""
        # Assuming 1 for correct and 0 for incorrect
        self.performance.append(1 if correct else 0)

    def current_status(self):
        """Calculates the current status of the flashcard based on performance."""
        if len(self.performance) == 0:
            return "Unattempted"
        avg_performance = sum(self.performance) / len(self.performance)
        if avg_performance > 0.8:
            return "Mastered"
        elif avg_performance > 0.5:
            return "Correct"
        else:
            return "Needs more work"


class FlashcardApp:
    def __init__(self):
        self.flashcards = []
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def add_flashcard(self, question, answer, category):
        self.flashcards.append(Flashcard(question, answer, category))
        print("Flashcard added.")

    def save_flashcards_to_json(self, filepath="flashcards.json"):
        with open(filepath, "w") as file:
            json_data = [flashcard.to_dict() for flashcard in self.flashcards]
            json.dump(json_data, file, indent=4)
        print("Flashcards saved to", filepath)

    def load_flashcards_from_json(self, filepath="flashcards.json"):
        try:
            with open(filepath, "r") as file:
                json_data = json.load(file)
                self.flashcards = [
                    Flashcard.from_dict(flashcard_data) for flashcard_data in json_data
                ]
            print("Flashcards loaded from", filepath)
        except FileNotFoundError:
            print("No saved flashcards found.")

    def compute_similarity(self, user_answer, correct_answer):
        user_embedding = self.model.encode(user_answer, convert_to_tensor=True)
        correct_embedding = self.model.encode(correct_answer, convert_to_tensor=True)
        cosine_scores = util.pytorch_cos_sim(user_embedding, correct_embedding)
        return cosine_scores.item()

    def quiz_by_category(self, category):
        category_flashcards = [fc for fc in self.flashcards if fc.category == category]
        if not category_flashcards:
            print(
                f"No flashcards available for category: {category}. Please add some flashcards first."
            )
            return
        random.shuffle(category_flashcards)
        correct_answers = 0
        for flashcard in self.flashcards:
            print(f"Category: {flashcard.category} - Question: {flashcard.question}")
            start_time = time.time()
            user_answer = input("Your answer: ")
            elapsed = time.time() - start_time
            print(f"Time taken: {elapsed:.2f} seconds")
            similarity = self.compute_similarity(user_answer, flashcard.answer)
            correct = similarity >= 0.7
            if correct:
                print("Correct!")
                correct_answers += 1
            else:
                print(f"Wrong! The correct answer was: {flashcard.answer}")
            flashcard.update_performance(correct)
            print(f"Status: {flashcard.current_status()}\n")

        print(f"You got {correct_answers}/{len(self.flashcards)} correct answers.")

    def quiz(self):
        categories = list(set(fc.category for fc in self.flashcards))
        if not categories:
            print("No flashcards available. Please add some flashcards first.")
            return
        category = questionary.select("Choose a category:", choices=categories).ask()
        self.quiz_by_category(category)

    def run(self):
        selected_json = self.select_json_file()
        self.load_flashcards_from_json(selected_json)
        while True:
            action = questionary.select(
                "Choose an action:",
                choices=["Add a flashcard", "Quiz yourself", "Save flashcards", "Exit"],
            ).ask()
            if action == "Add a flashcard":
                question = input("Enter the question: ")
                answer = input("Enter the answer: ")
                category = input("Enter the category: ")
                self.add_flashcard(question, answer, category)
            elif action == "Quiz yourself":
                self.quiz()
            elif action == "Save flashcards":
                self.save_flashcards_to_json(selected_json)
            elif action == "Exit":
                # Save flashcards before exiting
                self.save_flashcards_to_json(selected_json)
                print("Exiting the app. Goodbye!")
                break


if __name__ == "__main__":
    app = FlashcardApp()
    app.run()
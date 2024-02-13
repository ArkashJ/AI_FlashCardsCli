import json
import os
import random
import time

import questionary
import spacy
import torch
from colorama import Fore, Style
from sentence_transformers import SentenceTransformer, util
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from categorize_data import (categorize_flashcards,
                             load_flashcards_from_category,
                             save_categorized_flashcards_to_json)

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")


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
        for flashcard in category_flashcards:
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
        category = questionary.select(f"Choose a category:", choices=categories).ask()
        self.quiz_by_category(category)
        categories = categorize_flashcards(self.flashcards)
        save_categorized_flashcards_to_json(categories)

    def select_json_file(self):
        json_files = [f for f in os.listdir(".") if f.endswith(".json")]
        json_files.append("Create new JSON file")
        selected_file = questionary.select(
            "Choose a JSON file or create a new one:", choices=json_files
        ).ask()
        if selected_file == "Create new JSON file":
            new_filename = questionary.text("Enter new JSON filename:").ask()
            return (
                new_filename
                if new_filename.endswith(".json")
                else new_filename + ".json"
            )
        else:
            return selected_file

    def quiz_by_performance(self):
        file_path = "categorized_flashcards.json"
        category = questionary.select(
            "Choose a performance category:",
            choices=["Mastered", "Correct but Needs Practice", "Needs More Work"],
        ).ask()
        flashcards = load_flashcards_from_category(file_path, category)

        if not flashcards:
            print(
                f"No flashcards available for category: {category}. Please add some flashcards first."
            )
            return
        random.shuffle(flashcards)
        flashcard_objects = [Flashcard.from_dict(fc) for fc in flashcards]
        # You might need to adjust this part to fit how you want to quiz the user with these flashcards
        for flashcard in flashcard_objects:
            print(f"Category: {flashcard.category} - Question: {flashcard.question}")
            user_answer = input("Your answer: ")
            similarity = self.compute_similarity(user_answer, flashcard.answer)
            correct = similarity >= 0.7
            if correct:
                print("Correct!")
            else:
                print(f"Wrong! The correct answer was: {flashcard.answer}")
            flashcard.update_performance(correct)
            print(f"Status: {flashcard.current_status()}\n")

    def print_flashcards(self):
        random.shuffle(self.flashcards)
        for flashcard in self.flashcards:
            print(f"\n{Fore.CYAN}Category: {Style.RESET_ALL}{flashcard.category}")
            print(f"{Fore.GREEN}Question: {Style.RESET_ALL}{flashcard.question}")
            user_input = input("Press Enter to reveal the answer...")
            print(f"{Fore.MAGENTA}Answer: {Style.RESET_ALL}{flashcard.answer}")
            doc = nlp(flashcard.answer)
            keywords = [token.text for token in doc if token.pos_ in ["NOUN", "PROPN"]]

            print(f"{Fore.YELLOW}Keywords: {Style.RESET_ALL}{keywords}")
            # Prompt to move to the next question or exit the session
            proceed = questionary.confirm("Move to the next question?").ask()
            if not proceed:
                break

    def print_all_flashcards(self):
        for flashcard in self.flashcards:
            print(f"\n{Fore.CYAN}Category: {Style.RESET_ALL}{flashcard.category}")
            print(f"{Fore.GREEN}Question: {Style.RESET_ALL}{flashcard.question}")
            print(f"{Fore.MAGENTA}Answer: {Style.RESET_ALL}{flashcard.answer}")

    def write_to_txt(self, flashcard: Flashcard, file_name: str):
        with open(file_name, "a") as file:
            file.write(f"\nCategory: {flashcard.category}\n")
            file.write(f"Question: {flashcard.question}\n")
            file.write(f"Answer: {flashcard.answer}\n\n")

    def run(self):
        selected_json = self.select_json_file()
        self.load_flashcards_from_json(selected_json)
        while True:
            action = questionary.select(
                "Choose an action:",
                choices=[
                    "Add a flashcard",
                    "Quiz yourself",
                    "Quiz by performance",
                    "Save flashcards",
                    "Interactive print",
                    "print flashcards",
                    "Write to a file",
                    "Exit",
                ],
            ).ask()
            if action == "Add a flashcard":
                question = input("Enter the question: ")
                answer = input("Enter the answer: ")
                category = input("Enter the category: ")
                self.add_flashcard(question, answer, category)
            elif action == "Quiz by performance":
                self.quiz_by_performance()
            elif action == "Interactive print":
                self.print_flashcards()
            elif action == "print flashcards":
                self.print_all_flashcards()
            elif action == "Quiz yourself":
                self.quiz()
            elif action == "Write to a file":
                file_name = questionary.text("Enter the file name to write to:").ask()
                for flashcard in self.flashcards:
                    self.write_to_txt(flashcard, file_name)
                print(f"Flashcards written to {file_name}")
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

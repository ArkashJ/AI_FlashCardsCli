## Ideas to implement

# Classify the data into different categories

# Todo

- assign weights to each question
- use weights to calculate score
- Space repetition
- Make different json files
- add dropdown, quiz by category
- Look at the data and store it in a bucket
- Use LLM to predict how correct the data is, closeness validity is 70%
- Shuffle questions and answers
- Make buckets of data depending on how strong or weak you are on a topic
- Add a diagram
- Add a timer
- Add a score

# Run this locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 flashcards.py
```

# Or you can use docker

```bash
docker build -t ai_flashcards:latest .
docker run -it -p 4000:80 ai_flashcards
```

To stop the container

```bash
docker stop ai_flashcards
```

# Functionality

- Added spacy to download an english language model
  - the model finds keywords in my questions and answers
- Modified my print function to prompt the user for printing the answer after reading the question, printing the answer, showing keywords
  and then asking the user if they want to continue
- Added a function to calculate the score of the user
- Added a function to shuffle the questions and answers

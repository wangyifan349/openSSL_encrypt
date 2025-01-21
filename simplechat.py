# Import necessary libraries
from transformers import BertTokenizer, BertModel
import torch
import numpy as np
import faiss

# Initialize the BERT tokenizer and model
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')

# Define a function to encode a sentence using BERT
def encode_sentence(sentence):
    # Tokenize the input sentence and convert to tensors
    inputs = tokenizer(sentence, return_tensors='pt', truncation=True, padding=True, max_length=128)
    # Pass the inputs through the BERT model
    outputs = model(**inputs)
    # Extract the [CLS] token's embedding as the sentence representation
    cls_embedding = outputs.last_hidden_state[:, 0, :].detach().numpy()
    return cls_embedding

# Sample dictionary of medical and coding questions and answers
qa_pairs = {
    "What are the symptoms of COVID-19?": "Common symptoms include fever, dry cough, and tiredness. Some patients may also experience aches and pains, nasal congestion, sore throat, or diarrhea.",
    "How is hypertension diagnosed?": "Hypertension is diagnosed by measuring blood pressure over time. A diagnosis is usually made if blood pressure readings are consistently at or above 140/90 mmHg.",
    "What is the recommended treatment for type 2 diabetes?": "Treatment includes lifestyle changes such as diet and exercise, medication like metformin, and monitoring blood sugar levels regularly.",
    "What are the common causes of headaches?": "Common causes include stress, dehydration, lack of sleep, certain foods, and sometimes underlying medical conditions like migraines or sinusitis.",
    "How can I prevent heart disease?": "Prevention includes maintaining a healthy diet, engaging in regular physical activity, avoiding smoking, managing stress, and having regular health check-ups.",
    "What are the symptoms of a stroke?": "Symptoms include sudden numbness or weakness, especially on one side of the body, confusion, trouble speaking or understanding speech, and difficulty seeing in one or both eyes.",
    "How is asthma treated?": "Asthma is treated with inhalers that contain bronchodilators and steroids to reduce inflammation. Avoiding triggers and using a peak flow meter to monitor breathing is also important.",
    "What is the difference between a cold and the flu?": "The flu generally has more severe symptoms such as high fever, body aches, and extreme fatigue, while a common cold is milder and typically involves a runny nose and sore throat.",
    "What are the risk factors for osteoporosis?": "Risk factors include aging, hormonal changes (especially in women post-menopause), a diet low in calcium and vitamin D, and a sedentary lifestyle.",
    "How is depression diagnosed?": "Depression is diagnosed through clinical evaluation, which may involve interviews, questionnaires, and sometimes physical exams to rule out other conditions.",
    "What are the side effects of chemotherapy?": "Common side effects include nausea, vomiting, fatigue, hair loss, anemia, and increased risk of infections due to lowered white blood cell counts.",
    "How can I improve my mental health?": "Improving mental health can involve regular exercise, maintaining social connections, practicing mindfulness or meditation, managing stress, and seeking professional help if needed.",
    "What is the treatment for insomnia?": "Treatment options include lifestyle changes like improving sleep hygiene, cognitive behavioral therapy for insomnia (CBT-I), and sometimes medication prescribed by a healthcare provider.",
    "What are the benefits of regular exercise?": "Benefits include improved cardiovascular health, stronger muscles and bones, better mental health and mood, enhanced sleep quality, and weight management.",
    "What is the role of diet in managing cholesterol levels?": "A healthy diet low in saturated fats and trans fats and high in fiber-rich foods like fruits, vegetables, and whole grains can help manage cholesterol levels.",
    "How is anemia treated?": "Treatment depends on the cause but may include dietary changes to increase iron and vitamin intake, supplements, or medications to stimulate red blood cell production.",
    "What are the symptoms of an allergic reaction?": "Symptoms can include itching, swelling, difficulty breathing, hives, and, in severe cases, anaphylaxis, which requires immediate medical attention.",
    "How can I manage stress effectively?": "Effective stress management techniques include regular physical activity, meditation, deep breathing exercises, adequate sleep, and time management strategies.",
    "How do you create a virtual environment in Python?": "Use the command `python -m venv myenv` to create a virtual environment. Activate it with `source myenv/bin/activate` on macOS/Linux or `myenv\\Scripts\\activate` on Windows.",
    "How do you read a CSV file in Python?": "You can use the `pandas` library with `import pandas as pd` and then `df = pd.read_csv('file.csv')` to read a CSV file into a DataFrame.",
    "What is the purpose of the `if __name__ == '__main__':` statement in Python?": "It ensures that code inside the block only runs when the script is executed directly, not when imported as a module in another script.",
    "How do you handle exceptions in Python?": "Use a try-except block to handle exceptions. For example, `try: ... except Exception as e: print(e)` will catch and print exceptions.",
    "How do you write a function in Python?": "Define a function using the `def` keyword, followed by the function name and parentheses. For example, `def my_function():` followed by the function body."
}

# Encode all questions in the dictionary
question_embeddings = np.array([encode_sentence(q) for q in qa_pairs.keys()]).squeeze()

# Initialize a FAISS index for similarity search
d = question_embeddings.shape[1]  # Dimension of the embeddings
index = faiss.IndexFlatL2(d)      # Use L2 distance for the index
index.add(question_embeddings)    # Add the question embeddings to the index

# Function to find the top k most similar questions and provide their answers
def find_top_k_similar_questions(query, k=1):
    # Encode the query using BERT
    query_embedding = encode_sentence(query).squeeze()
    # Search the FAISS index for the top k nearest neighbors
    D, I = index.search(query_embedding.reshape(1, -1), k)
    # Retrieve the top k most similar questions and their corresponding answers
    results = []
    for i in range(k):
        similar_question = list(qa_pairs.keys())[I[0][i]]
        similarity_score = 1 / (1 + D[0][i])  # Convert L2 distance to a similarity score
        results.append((similar_question, qa_pairs[similar_question], similarity_score))
    return results

# Test the question-answering system with a query
query = "How can I manage high blood pressure?"
top_k_results = find_top_k_similar_questions(query, k=2)

# Print the results
print(f"Query: {query}")
for idx, (matched_question, answer, score) in enumerate(top_k_results, start=1):
    print(f"\nTop {idx} Match:")
    print(f"Matched Question: {matched_question}")
    print(f"Answer: {answer}")
    print(f"Similarity Score: {score:.4f}")

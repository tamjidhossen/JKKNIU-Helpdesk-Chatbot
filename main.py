from dotenv import load_dotenv
import os

load_dotenv()

from langchain_ollama.llms import OllamaLLM
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import time
from vector import retriever
from config import LLM_MODEL, CHATBOT_TEMPLATE

# model = OllamaLLM(model=LLM_MODEL)
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

template = CHATBOT_TEMPLATE

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

while True:
    print("\n\n-------------------------------")
    question = input("Ask your question (q to quit): ")
    print("\n\n")
    if question == "q":
        break
    
    # context = []
    context = retriever.invoke(question)
    start_time = time.time()
    result = chain.invoke({"context": context, "question": question})
    elapsed_time = time.time() - start_time
    print(result.content)
    print(f"Response time: {elapsed_time:.2f} seconds")

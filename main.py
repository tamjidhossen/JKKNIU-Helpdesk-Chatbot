from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import time
from vector import retriever
from config import LLM_MODEL, CHATBOT_TEMPLATE

model = OllamaLLM(model=LLM_MODEL)

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
    print(result)
    print(f"Response time: {elapsed_time:.2f} seconds")

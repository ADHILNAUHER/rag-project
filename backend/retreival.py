import os
from typing import Dict, Optional, List
from dotenv import load_dotenv

# --- NEW/MODIFIED IMPORTS ---
from huggingface_hub import InferenceClient
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

# --- END NEW/MODIFIED IMPORTS ---

from backend.ingestion import _get_vectorstore
from langchain_core.documents import Document
from pathlib import Path

# Ensure .env variables are loaded
load_dotenv()

# --- NEW: Initialize the client, just like in your state.py ---
# Note: Ensure your .env file has HUGGINGFACEHUB_API_TOKEN
# (or HUGGINGFACE_API_TOKEN as seen in your state.py)
client = InferenceClient(
    model="meta-llama/Meta-Llama-3.1-8B-Instruct",
    token=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
)


def _get_llm_chain():
    """
    Creates a custom LangChain runnable (a "Lambda") that
    calls the Hugging Face InferenceClient and *streams* the response.
    """

    def stream_llm(prompt_value):
        """
        Takes the output from the prompt template (a ChatPromptValue),
        formats it, and *yields* tokens from the InferenceClient.
        """
        # 1. Convert LangChain messages to the dict list
        messages = []
        for msg in prompt_value.to_messages():
            if isinstance(msg, SystemMessage):
                messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                messages.append({"role": "assistant", "content": msg.content})

        try:
            # 2. Call the client with stream=True
            stream = client.chat_completion(
                messages=messages,
                max_tokens=550,
                stop=["<|eot_id|>"],  # <-- Good to re-enable this
                stream=True,
            )

            # 3. Yield each token as it arrives
            print("\n--- [DEBUG] Streaming response from LLM... ---")
            for token in stream:
                if token.choices and token.choices[0].delta.content:
                    chunk = token.choices[0].delta.content
                    yield chunk
            print("\n--- [DEBUG] Stream finished. ---")

        except Exception as e:
            print(f"\nError calling Hugging Face client: {e}")
            yield "Sorry, I ran into an error trying to generate a response."

    # 4. Wrap the streaming generator in a RunnableLambda
    return RunnableLambda(stream_llm)


def _get_retrieval_chain(file_id: Optional[str] = None):
    """
    Constructs a RAG chain using the custom InferenceClient runnable.
    """
    vectorstore = _get_vectorstore()

    search_kwargs = {"k": 79}
    if file_id:
        print(f"Retrieval chain: Filtering by file_id: {file_id}")
        search_kwargs["filter"] = {"file_id": str(file_id)}
    else:
        print("Retrieval chain: No file_id, searching all documents.")

    retriever = vectorstore.as_retriever(
        search_type="similarity", search_kwargs=search_kwargs
    )

    # --- (THIS IS STILL 100% CORRECT) ---
    # We still need the Llama 3 Chat Template to format the
    # messages *before* they go to our custom LLM function.

    system_template = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are a helpful assistant. Answer the user's question based on the following context, and also from your own knowledge.
If the answer is not found in the context, never say "I could not find an answer in the document."
If answer is not found in the context, try to respond from your own knowledge.
Keep your answers concise and to the point, and professional.

---
**Formatting Instructions:**
Format your final answer using clear and concise Markdown,try to keep the answer medium length.
- Use headings (`##` or `###`) for main topics.
- Use bold white (`**text**`) to emphasize key terms.
- Use bullet points (`* item`) for lists or key points.
- Use numbered lists (`1. item`) for steps or sequences.
---

Context:
{context}<|eot_id|>"""

    human_template = """<|start_header_id|>user<|end_header_id|>
Question:
{question}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template(human_template),
        ]
    )
    # --- END (STILL CORRECT) ---

    # Get our new custom LLM chain
    llm_chain = _get_llm_chain()

    def format_docs(docs: list) -> str:
        return "\n\n".join(doc.page_content for doc in docs)

    def log_retrieved_docs(docs):
        print("\n--- [DEBUG] RETRIEVED DOCUMENTS ---")
        if not docs:
            print("!!! [DEBUG] NO DOCUMENTS WERE RETRIEVED !!!")
        for i, doc in enumerate(docs):
            print(f"--- [DEBUG] Doc {i+1} (file_id: {doc.metadata.get('file_id')}) ---")
            print(doc.page_content[:200] + "...")
        print("-------------------------------------\n")
        return docs

    rag_chain = (
        {
            "context": retriever | RunnableLambda(log_retrieved_docs) | format_docs,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm_chain
    )

    return rag_chain


def get_streaming_answer(query: str, file_id: Optional[str] = None):
    """
    Given a query and file_id, returns a *generator* that yields the RAG answer.
    """
    chain = _get_retrieval_chain(file_id=file_id)
    return chain.stream(query)

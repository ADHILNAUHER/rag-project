# 🧠 RAG-Project

An end-to-end **AI-powered chat application** that can intelligently respond to user queries and retrieve information from uploaded documents using **Retrieval-Augmented Generation (RAG)**.  

This project demonstrates the seamless integration of **LLMs**, **vector databases**, and **modern full-stack tools** to build an interactive, document-aware AI assistant.

---

## 🚀 Overview

**RAG-Project** enables users to:
- Chat with an AI assistant powered by a large language model (LLM).  
- Upload documents (PDFs, text files, etc.) and query their contents conversationally.  
- Store and retrieve document embeddings for context-aware responses.  

It combines **semantic search** with **generative AI** to provide responses that are both **accurate** and **contextually relevant**.

---

## 🧩 Architecture

The project follows a modular, full-stack design:

### 🖥️ Frontend
- **Framework:** [Reflex (Python)](https://reflex.dev/)  
- **Purpose:** Provides an intuitive chat interface for users to interact with the AI.  
- **Key Features:**  
  - Upload documents through the UI.  
  - Display AI responses and document references.  
  - Real-time chat updates.

### ⚙️ Backend
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)  
- **Purpose:** Handles API routes, document ingestion, and communication with external services.  
- **Key Features:**  
  - Processes uploaded files and stores metadata in **PostgreSQL**.  
  - Generates embeddings using **Hugging Face Inference API**.  
  - Stores and retrieves vector representations using **Pinecone**.  
  - Performs context retrieval and feeds it into the **LLM** for final response generation.

---

## 🧠 How It Works

1. **User uploads a document** via the frontend.  
2. **Backend extracts text** and sends it to the **Hugging Face Embeddings API** to generate vector embeddings.  
3. These embeddings are stored in **Pinecone**, a high-performance vector database.  
4. When a user asks a question, the query is embedded in the same vector space.  
5. **Relevant document chunks** are retrieved from Pinecone based on similarity search.  
6. The retrieved context is combined with the query and sent to the **Hugging Face LLM API**.  
7. The LLM generates a **context-aware answer**, which is sent back to the user in the chat interface.  

This architecture ensures the model’s responses are grounded in **your own data**, not just general knowledge.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-------------|
| **Frontend** | Python Reflex |
| **Backend** | FastAPI |
| **Database** | PostgreSQL |
| **Vector Store** | Pinecone |
| **Embeddings** | Hugging Face Inference API |
| **LLM** | Hugging Face Inference API |
| **Architecture** | Retrieval-Augmented Generation (RAG) |

---

## 🗂️ Project Structure
```
rag-project/
├── rag_project/
|    ├── rag_project.py
|    ├── file_card.py
|    ├── chat.py
|    ├── state.py
|    └── style.py
├── backend/
│    ├── main.py
|    ├── retrieval.py
│    └── ingestion.py
├── .env
├── requirements.txt
├── .gitignore
└── README.md
```
## 📽️ Video Demo


https://github.com/user-attachments/assets/4628eb9b-7f08-4aa7-b78e-192b3fe40003


# FastAPI Custom Backend API Documentation

## 1. Overview

A custom backend API was developed using **FastAPI** to act as an intermediate layer between OpenWebUI and Ollama. The backend exposes **OpenAI-compatible API endpoints**, allowing OpenWebUI to communicate with a local language model without connecting directly to Ollama.

The implementation consisted of two stages:

1. Connecting **FastAPI** with **Ollama** by implementing OpenAI-compatible endpoints.
2. Configuring **OpenWebUI** to use the custom FastAPI backend and verifying end-to-end communication.

---

## 2. Technology Stack

| Technology | Purpose |
|------------|---------|
| FastAPI | Backend API development |
| Python | Programming language |
| Pydantic | Request validation and schema management |
| Uvicorn | Running the FastAPI server |
| Ollama | Local LLM inference |
| OpenWebUI | Chat interface |
| Docker | Running OpenWebUI |
| Postman | API testing |
| Git/GitHub | Version control |

---

## 3. FastAPI Application Setup

The FastAPI application was configured and executed using Uvicorn.

Command used:

```bash
uvicorn app.main:app --reload
```

The server started successfully and was accessible for API testing.


![FastAPI Server](images/fastapi-server-running.PNG)

---

## 4. Connecting FastAPI with Ollama

The FastAPI backend was connected to Ollama to forward chat requests to the local language model.

Two OpenAI-compatible endpoints were implemented:

```
GET /v1/models
POST /v1/chat/completions
```

These endpoints allow clients to retrieve available models and generate chat responses using Ollama.

---

## 5. API Testing Using Postman

The implemented endpoints were tested using **Postman** before integrating OpenWebUI.

### 5.1 Model Endpoint Verification

The `GET /v1/models` endpoint was tested to verify that the FastAPI backend could successfully retrieve the available Ollama models.


![Available Models](images/models-check.png)

---

### 5.2 Chat Completion Endpoint Verification

The `POST /v1/chat/completions` endpoint was tested by sending:

- Model name
- User message

The backend successfully processed the request through Ollama and returned an OpenAI-compatible response.



![POST Endpoint Test](images/check-post-endpoint.png)

---

### 5.3 Model Response Verification

Additional testing confirmed that the selected model was responding correctly through the FastAPI backend.


![Model Verification](images/model-check-postman.png)

---

## 6. Request Processing Flow

The request flow through the custom backend is shown below.

```
Client Request
      │
      ▼
FastAPI Endpoint
      │
      ▼
Request Validation
      │
      ▼
Ollama
      │
      ▼
OpenAI-Compatible Response
```

---

## 7. OpenAI-Compatible Response Format

Responses were returned using the OpenAI Chat Completion API format.

Example response:

```json
{
  "id": "chatcmpl-1",
  "object": "chat.completion",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "response text"
      }
    }
  ]
}
```

This format enables compatibility with clients such as OpenWebUI.

---

## 8. Request Validation

Pydantic models were used to validate incoming requests.

Validation includes:

- Required fields
- Request structure validation
- Automatic error handling

Example validation error:

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": [
        "body",
        "username"
      ],
      "msg": "Field required"
    }
  ]
}
```

---

## 9. OpenWebUI Integration

After verifying the FastAPI endpoints, OpenWebUI was configured to use the custom FastAPI backend instead of connecting directly to Ollama.

The integration was verified by sending chat messages through OpenWebUI and receiving responses generated through the FastAPI backend.

### FastAPI Connection

![FastAPI Connection](images/fast-api-connection-check.png)

### Chat Verification

![Chat Verification](images/chat-check.png)

---

## 10. Docker Verification

The OpenWebUI Docker container was verified to be running successfully during integration.


![Docker Container Status](images/docker-image-check.png)

---

## 11. Git Version Control

The completed implementation was tracked using Git and pushed to the project repository.

Changes included:

- FastAPI backend setup
- OpenAI-compatible endpoint implementation
- Ollama integration
- Postman API testing
- OpenWebUI integration
- Documentation updates

---
You can add this as a small section at the end of your documentation.

---

## Update: Migrated from Ollama to Gemini

Initially, the OpenAI-compatible FastAPI backend was integrated with **Ollama** for local inference. During testing, response generation was noticeably slower, especially when accessed through OpenWebUI. To improve responsiveness and provide a smoother user experience, the backend was migrated to **Google Gemini** using the **Google GenAI SDK**.

The integration now follows the flow:

```text
OpenWebUI → FastAPI (OpenAI-compatible API) → Gemini API
```

Streaming responses were also implemented so that responses are displayed token-by-token in OpenWebUI instead of waiting for the complete output.

### Verification

The following tests were performed successfully:

* **GET `/v1/models`** – Verified that the FastAPI backend exposes the available Gemini model.


![response in Postman](images/get.png)
  

* **POST `/v1/chat/completions`** – Verified successful communication between FastAPI and Gemini using the OpenAI-compatible endpoint.

![response in Postman](images/post.png)


* **OpenWebUI Chat** – Verified that OpenWebUI communicates with the FastAPI backend and receives **streaming responses** from Gemini.

![response in Postman](images/chat_check.png)

  
This migration resulted in faster response times and real-time streaming while preserving the OpenAI-compatible interface for OpenWebUI.

# Summary

Completed work:

- ✅ Set up the FastAPI backend
- ✅ Connected FastAPI with Ollama
- ✅ Implemented the `GET /v1/models` endpoint
- ✅ Implemented the `POST /v1/chat/completions` endpoint
- ✅ Tested both endpoints using Postman
- ✅ Verified available Ollama models
- ✅ Configured OpenWebUI to use the FastAPI backend
- ✅ Verified end-to-end chat through OpenWebUI
- ✅ Verified Docker container execution
- ✅ Managed changes using Git/GitHub
- ✅ Verified Gemini model.
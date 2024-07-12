# CoLearner

CoLearner is an intelligent assistant that converses with your personal knowledge base, including books, websites, notes, codes, etc. It's designed to provide information search and learning assistance for continuous learning throughout your career.

Built with Langchain using pretrained LLM and RAG pipeline.
App is built with Streamlit and served on GCP.


## Features

| Feature | Description |
|---------|-------------|
| All in one place | All information about what you have learned and worked on in once place |
| Personal Knowledge Chat | Engage in conversations with an AI that understands your learning and work history |
| Information Retrieval | Quickly find relevant information from your personal knowledge base |
| Learning Assistant | Automatically make a review and recap plan based on recent learning |
| Progress Tracking | Monitor your learning journey across various subjects and skills |


## Getting Started


## Development Plan

| Feature | Description | Progress |
|---------|-------------|----------|
| Project initialization | Set up project structure and dev environment |🟢 Completed |
| Data Ingestion | Develop system to import data from various sources:<br>&nbsp;&nbsp; - Website<br>&nbsp;&nbsp; - Notion <br>&nbsp;&nbsp; - Git repository<br>&nbsp;&nbsp;&nbsp;&nbsp; - Github<br>&nbsp;&nbsp; - Youtube <br>&nbsp;&nbsp; - Local files<br> |  🟡 In Progress |
| First prototype | Implement a basic chatbot with RAG| 🟢 Completed |
| RAG refinement | Improve RAG pipeline performance: <br>&nbsp;&nbsp; - Splitter <br>&nbsp;&nbsp; - Embedding <br>&nbsp;&nbsp; - Retrieval method| 🔴 Not Started |
| Routing | Design routing | 🔴 Not Started |
| Agents | Develope agents needed to create study plan and track progress | 🔴 Not Started |
| Web App | Develop a web app with Streamlit | 🟢 Completed |
| Deployment | Hosted on GCP | 🟡 In Progress |
| Local deployment | Instructions on local deployment | 🔴 Not Started |


## Configure

Create a `.env` file from the environment template file `env.example`

Available variables:
| Variable Name          | Default value                      | Description                                                             |
|------------------------|------------------------------------|-------------------------------------------------------------------------|
| OLLAMA_BASE_URL        | http://host.docker.internal:11434  | REQUIRED - URL to Ollama LLM API                                        |   
| LLM                    | llama2                             | REQUIRED - Can be any Ollama model tag, or gpt-4 or gpt-3.5             |
| EMBEDDING_MODEL        | sentence_transformer               | REQUIRED - Can be sentence_transformer, openai, aws, ollama or google-genai-embedding-001|
| OPENAI_API_KEY         |                                    | REQUIRED - Only if LLM=gpt-4 or LLM=gpt-3.5 or embedding_model=openai   |
| LANGCHAIN_ENDPOINT     | https://api.smith.langchain.com  | OPTIONAL - URL to Langchain Smith API                                   |
| LANGCHAIN_TRACING_V2   | false                              | OPTIONAL - Enable Langchain tracing v2                                  |
| LANGCHAIN_PROJECT      |                                    | OPTIONAL - Langchain project name                                       |
| LANGCHAIN_API_KEY      |                                    | OPTIONAL - Langchain API key                                            |


## Contributing

We welcome contributions to MindWhisperer! 

## License

This project is licensed under the [MIT License](LICENSE).
# AI RAG Widget ⭐

> 🤖 Интеллектуальный RAG-чат-виджет для ответов по документам компании.

RAG (Retrieval-Augmented Generation) сервис, который загружает документы компании (PDF, DOCX, TXT), индексирует их в векторную базу ChromaDB и отвечает на вопросы пользователей на основе содержимого документов через LLM.

[![Tests](https://github.com/umowork/ai-rag-widget/actions/workflows/ci.yml/badge.svg)](https://github.com/umowork/ai-rag-widget/actions)

---

## ✨ Возможности

- 📄 **Загрузка документов**: PDF, DOCX, TXT, MD, plain text
- 🔍 **Semantic search**: Vector поиск по ChromaDB + cross-encoder reranking
- 💬 **Чат**: Синхронный и стриминг (SSE) режимы
- 🧩 **Встраиваемый JS виджет**: Добавляется на сайт в 2 строки HTML
- 🔌 **LLM провайдеры**: OpenAI GPT, YandexGPT, Mock (для тестов)
- 🧠 **Embedding провайдеры**: HuggingFace (локально) или OpenAI
- ⚡ **Кэширование ответов**: In-memory кэш с TTL
- 🐳 **Docker**: Готовая multi-stage сборка

## 🚀 Быстрый старт

```bash
# 1. Установка
git clone <repo>
cd ai-rag-widget
cp .env.example .env
# Редактируем .env: MOCK_MODE=true для теста без API ключей

# 2. Зависимости
make dev-install

# 3. Тесты
make test

# 4. Запуск
make run
# → http://localhost:8000/docs (Swagger)
```

## 🔧 Конфигурация

Основные переменные окружения (см. `.env.example`):

| Переменная | По умолчанию | Описание |
|-----------|-------------|---------|
| `LLM_PROVIDER` | `openai` | `openai`, `yandexgpt`, или `mock` |
| `OPENAI_API_KEY` | — | API ключ OpenAI |
| `EMBEDDING_PROVIDER` | `huggingface` | `huggingface` или `openai` |
| `MOCK_MODE` | `false` | `true` = использовать MockLLM |
| `CHROMA_DB_DIR` | `./chroma_db` | Директория ChromaDB |

## 📡 API

| Метод | Путь | Описание |
|-------|------|---------|
| `GET` | `/health` | Статус сервиса |
| `POST` | `/chat` | Синхронный Q&A |
| `GET` | `/chat/stream` | Стриминг Q&A (SSE) |
| `POST` | `/upload/text` | Загрузка текста |
| `POST` | `/upload/file` | Загрузка файла |
| `GET` | `/widget.js` | JS виджет |

## 🧪 Тесты

```bash
make test        # 50+ тестов, 8 файлов
make test-cov    # С coverage отчётом
```

## 🐳 Docker

```bash
make docker-build
make docker-up
# → http://localhost:8000
```

## 🏗 Архитектура

```
FastAPI ← RAGEngine ← VectorStoreService (ChromaDB)
                  ↕
            LLMService (OpenAI / YandexGPT / Mock)
                  ↕
            DocumentProcessor → TextSplitter → EmbeddingService
```

**Модульная структура:**
- `models/` — Pydantic схемы
- `services/` — Бизнес-логика (6 сервисов)
- `api/` — Route handlers
- `rag_engine.py` — Центральный координатор

**Lazy imports** для тяжелых библиотек: `torch`, `sentence-transformers`, `chromadb`, `openai`, `pypdf`, `python-docx`.

## 📦 Технологии

- Python 3.12 + FastAPI
- ChromaDB (vector store)
- LangChain-free (собственная реализация RAG)
- sentence-transformers / OpenAI embeddings
- Vanilla JS виджет (0 зависимостей)

---

*Built with AI assistance. Portfolio project — не для продакшена без аудита.*

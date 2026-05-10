# ROADMAP — 06 ai-rag-widget

## Шаг 1 — Backend ingestion

- [ ] Структура: `apps/api`, `apps/widget`, `docker-compose.yml`
- [ ] FastAPI + LangChain + ChromaDB
- [ ] `POST /docs` — загрузка PDF/MD/TXT
- [ ] Recursive chunking + overlap
- [ ] Embeddings + сохранение в ChromaDB

## Шаг 2 — Chat endpoint

- [ ] `POST /chat` — synchronous RAG
- [ ] Top-5 retrieval
- [ ] Промпт-шаблон с указанием источника
- [ ] System prompt против галлюцинаций
- [ ] Тесты на эталонных вопросах

## Шаг 3 — Multi-LLM gateway (РФ-приоритет)

- [ ] YandexGPT embeddings + chat
- [ ] GigaChat integration
- [ ] OpenAI fallback
- [ ] Выбор через env-переменную
- [ ] Embedding cache в Redis

## Шаг 4 — SSE streaming

- [ ] `GET /chat/stream` через SSE
- [ ] Прогресс retrieval → generation
- [ ] Rate limiting через slowapi

## Шаг 5 — Vanilla JS виджет

- [ ] `widget.js` — обёртка
- [ ] UI: floating button + chat panel
- [ ] Подключение через `<script>` + config
- [ ] Streaming через EventSource
- [ ] Темизация (цвета, шрифты)
- [ ] Адаптив

## Шаг 6 — Next.js админка + деплой

- [ ] Next.js + Tailwind админка для загрузки документов
- [ ] Админка: список документов, загрузка, удаление, просмотр чанков
- [ ] Админка: аналитика (частые вопросы, retrieval stats)
- [ ] Endpoint `DELETE /docs/{id}`
- [ ] Тесты core
- [ ] Docker compose (FastAPI + Next.js)
- [ ] Deploy на Fly.io
- [ ] Widget CDN через R2
- [ ] Demo-сайт с тестовыми документами
- [ ] README с реальными метриками (latency, accuracy, cost)
- [ ] Loom-демка
- [ ] Tag `v1.0.0`

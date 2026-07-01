# MenuIQ Interview Prep Q/A

## 1. Project Overview

### Q: Walk me through MenuIQ.

MenuIQ is a full-stack AI analytics application for restaurant menu optimization. The backend loads restaurant transaction data from PostgreSQL or from user-uploaded CSV/Excel files, computes deterministic analytics with Pandas, and then uses an LLM through LangChain to explain those results through recommendations and chat.

The key design decision is that the LLM is not the source of truth. The backend computes metrics like units sold, margin, menu-engineering quadrant, support, confidence, and lift. The LLM only explains and packages those computed facts into recommendations or chat answers.

### Q: What problem does MenuIQ solve?

MenuIQ helps restaurants understand which menu items are performing well, which items need promotion, which items may need pricing or margin improvements, and which items are good candidates for combos based on actual ordering behavior.

### Q: Why is this relevant to a Generative AI Application role?

MenuIQ shows how to build an AI application where the model is integrated responsibly into a real data workflow. The LLM is grounded in deterministic analytics, uses controlled tools instead of raw database access, returns structured outputs where needed, and is wrapped in a full-stack application with APIs, validation, session handling, and frontend visualization.

## 2. Architecture And Request Flow

### Q: Draw me the architecture. Trace one request from raw transaction data to a recommendation on screen.

Restaurant data enters either from PostgreSQL or from a CSV/Excel upload. The backend converts that data into Pandas DataFrames, computes menu engineering and market basket analytics, formats those facts, sends them to the LLM, receives structured recommendations, and returns JSON to the React frontend.

Flow:

```text
Restaurant transaction data
↓
PostgreSQL or uploaded CSV/Excel
↓
FastAPI backend
↓
Pandas analytics pipeline
↓
Menu engineering + market basket analysis
↓
Formatted analytics facts
↓
LLM recommendation generation
↓
FastAPI JSON response
↓
React frontend
↓
Recommendation card appears on screen
```

The important point is that the LLM does not calculate the business metrics. It receives already-computed facts and turns them into business-readable recommendations.

### Q: How does the React frontend talk to the backend?

The React frontend communicates with the FastAPI backend through REST API calls using `fetch`. The frontend has an API helper layer that calls endpoints like:

```text
GET /menu-matrix
GET /associations
GET /menu-analysis
POST /chat
POST /upload
```

The backend returns JSON validated by Pydantic schemas. The frontend stores those responses in React state and renders the quadrant chart, association table, recommendation cards, upload summary, and chat messages.

### Q: What does a typical API response look like?

For menu matrix:

```json
{
  "items": [
    {
      "item_id": 1,
      "name": "Classic Burger",
      "category": "main",
      "units_sold": 120,
      "margin": 7.0,
      "quadrant": "Star"
    }
  ],
  "popularity_threshold": 65.0,
  "margin_threshold": 4.5
}
```

For associations:

```json
{
  "pairs": [
    {
      "antecedent_name": "Classic Burger",
      "consequent_name": "Truffle Fries",
      "support": 0.12,
      "confidence": 0.65,
      "lift": 2.4
    }
  ]
}
```

For chat:

```json
{
  "answer": "Lobster Roll is a Puzzle, so it has high margin but lower popularity. I would promote it rather than cut it.",
  "structured_data": {
    "items": ["Lobster Roll"],
    "quadrants": ["Puzzle"]
  }
}
```

## 3. Backend And API Design

### Q: Why FastAPI? Why not Flask or Django?

I chose FastAPI because MenuIQ is primarily an API-driven Python application. The React frontend talks to the backend through REST endpoints, and FastAPI gives strong support for typed request/response models, Pydantic validation, dependency injection, and automatic OpenAPI documentation.

Flask could work, but I would have to add more validation, schema handling, and documentation manually. Django is powerful, but it is heavier and more full-stack than I needed. Since the frontend is React and the backend is mainly an API service for analytics and AI, FastAPI was a better fit.

### Q: What did async buy you here?

Async mainly helps in the upload endpoint because reading an uploaded file is I/O-bound. FastAPI’s file reading API uses `await file.read()`, so the route is `async def`. That lets the server avoid blocking unnecessarily while waiting for file data.

I would be honest that async does not speed up the Pandas analytics itself, because Pandas computation is CPU-bound and synchronous. For production, large uploads or heavy analytics should move to background workers.

### Q: Why PostgreSQL over something else?

PostgreSQL fits because the data is relational. MenuIQ has menu items, orders, and order lines. One order has many order lines, and each order line references a menu item. PostgreSQL gives schema integrity, joins, reliable storage, and easy integration with Pandas through SQLAlchemy.

### Q: What did your database schema look like?

The main tables were:

```text
menu_items
- item_id
- name
- price
- food_cost
- category
- margin

orders
- order_id
- ordered_at

order_lines
- line_id
- order_id
- item_id
- unit_price
```

`menu_items` stores the menu catalog. `orders` stores each transaction. `order_lines` connects orders to the items sold in each order. This supports both units-sold analysis and market basket analysis.

## 4. Pandas Analytics Pipeline

### Q: Walk me through the Pandas/NumPy pipeline step by step.

The pipeline starts by loading data from PostgreSQL or normalizing an uploaded CSV into canonical DataFrames. The item catalog contains item-level fields like name, price, food cost, category, and margin. The order-line table contains one row per sold unit with order ID and item ID.

For menu engineering, the pipeline groups order lines by item ID to count units sold, merges those counts into the item catalog, computes average popularity and margin thresholds, and classifies each item into Star, Plowhorse, Puzzle, or Dog.

For market basket analysis, the pipeline groups order lines by order ID into baskets, counts item co-occurrences, and calculates support, confidence, and lift for each item pair. The computed DataFrames are then cached and formatted into concise facts for the LLM to explain.

### Q: What does menu engineering do?

Menu engineering classifies each item by popularity and profitability. It compares each item’s units sold and margin against the menu-wide average or median.

```text
High popularity + high margin = Star
High popularity + low margin = Plowhorse
Low popularity + high margin = Puzzle
Low popularity + low margin = Dog
```

This gives the restaurant an actionable framework for protecting strong items, promoting profitable but under-selling items, improving margins on popular low-margin items, and reconsidering weak items.

### Q: For Burger, are you comparing it to the mean of all items?

Yes. If the threshold mode is mean, Burger’s units sold are compared against the average units sold across all menu items, and Burger’s margin is compared against the average margin across all menu items.

If Burger is above both averages, it is a Star. If it is above popularity but below margin, it is a Plowhorse. If it is below popularity but above margin, it is a Puzzle. If it is below both, it is a Dog.

### Q: What does market basket analysis do?

Market basket analysis finds which items customers tend to buy together. The backend groups order lines by order ID so each order becomes a basket of items. It then counts how often item pairs appear together and computes support, confidence, and lift.

Support tells how common a pair is across all orders. Confidence tells how often item B appears when item A is ordered. Lift tells whether the pairing is stronger than B’s normal baseline popularity.

### Q: Explain grouping order lines by order ID and counting co-occurrences.

An order line is one item inside a customer order. For example:

```text
order_id | item
101      | Burger
101      | Fries
101      | Soda
102      | Burger
102      | Fries
```

Grouping by order ID turns that into baskets:

```text
101 → {Burger, Fries, Soda}
102 → {Burger, Fries}
```

Co-occurrence means two items appeared in the same order. If Burger and Fries appear together in many baskets, their co-occurrence count is high. That count is then used to calculate support, confidence, and lift.

### Q: Were cross-selling opportunities computed statistically or interpreted by the LLM?

They were computed statistically in the backend. The backend groups order lines by order ID, counts item co-occurrences, and calculates support, confidence, and lift. Pairs with strong lift and confidence become cross-selling opportunities. The LLM only turns those computed patterns into business language, such as suggesting a combo or menu placement change.

## 5. Uploaded Data And Ingestion

### Q: How does uploaded data work?

The user uploads a CSV or Excel file. The backend reads it into Pandas, maps flexible column names into a canonical schema, validates required fields, builds an item catalog and order-line table, creates an isolated session for that upload, and runs the same analytics pipeline used for the demo data.

### Q: How did you handle messy input: missing fields, duplicates, inconsistent item names?

I handled messy input in the ingestion layer before data reached analytics or the LLM. I mapped flexible column names like `Product`, `Item`, or `Description` into a canonical `item_name` field, and `Order ID`, `Receipt`, or `Transaction ID` into `order_id`.

Required fields like order ID, item name, and price are validated. Invalid rows missing item name, order ID, or price are dropped with warnings. For profitability, the file must contain food cost, margin, or a user-provided assumed cost percentage.

I did not blindly remove duplicate transaction rows because repeated rows can represent real multiple items sold. In production, I would add deduplication only if the file had reliable unique transaction or line IDs.

### Q: What if the uploaded file has no food cost or margin?

The app lets the user provide an assumed food-cost percentage. If the file has no food cost or margin, the backend uses that explicit user assumption to derive margin. The system returns a warning that margin is based on the assumption, not actual cost data.

This is better than letting the LLM guess costs.

### Q: What are `line_id`, `order_id`, `item_id`, and `unit_price`?

`line_id` uniquely identifies each row in the order-line table. `order_id` identifies which customer order the item belongs to. `item_id` links the sold item back to the menu catalog. `unit_price` stores the sale price for one unit of that item.

This structure supports units-sold counts and market basket analysis because items in the same `order_id` are treated as being bought together.

## 6. AI Layer And LangChain

### Q: Why LangChain at all? Why not just call the OpenAI API directly?

I could have called the LLM API directly for a simple prompt-response chatbot. But MenuIQ needed more than that. It needed tool calling, structured recommendation output, prompt templates, and chat memory.

LangChain helped connect the LLM to the rest of the application. It let the model call safe analytics tools, use precomputed data, return structured outputs, and support session-based chat memory. With direct API calls, I would have had to manually build tool schemas, prompt formatting, response validation, and memory handling.

### Q: How can I say that without using “orchestration”?

I would say:

> LangChain helped manage the application logic around the model. The model had to work with backend analytics tools, receive trusted computed facts, return structured recommendation data, and support chat memory. A direct API call would work for a simple chatbot, but MenuIQ needed the model to interact with tools and structured analytics results.

### Q: Which LangChain components did you use?

I used LangChain in two main workflows:

1. A structured recommendation chain.
2. A tool-calling chat agent.

For recommendations, I used prompt templates and structured output with a Pydantic schema. For chat, I used LangChain tools, an agent, and LangGraph-style in-memory checkpointing for session memory.

### Q: What is an LLM chain?

An LLM chain is a fixed sequence of steps:

```text
input data → prompt template → LLM → output
```

The model is not deciding which tool to use. The workflow is predefined by code. In MenuIQ, the recommendation flow is a chain because the backend always computes analytics, formats facts, sends them to the LLM, and expects structured recommendation JSON.

### Q: Was MenuIQ actually an agent or just a chain?

MenuIQ has both. The recommendation cards are generated by a chain. The chat feature is a tool-calling agent.

The recommendation flow is fixed: analytics facts go into a prompt and the LLM returns structured recommendations. The chat flow is dynamic: the model can decide whether to call tools like item stats, item associations, or full menu matrix based on the user’s question.

It is not an autonomous execution agent that changes menus or prices. It is an advisory analytics agent.

### Q: Why not LlamaIndex?

LlamaIndex could work, especially if the app focused on retrieval over documents. But MenuIQ’s core data is structured transaction data, and the main need was calling deterministic analytics tools and generating structured recommendations. LangChain’s tool-calling and structured-output workflow fit better.

If I later added unstructured sources like customer reviews, supplier contracts, menu PDFs, or promotion notes, LlamaIndex or another RAG layer could become useful.

### Q: Which model/provider did you use?

The current implementation uses Groq through `langchain-groq`, with a Llama 3.3 70B model configured behind a shared model creation function. The provider is abstracted, so it could be swapped for OpenAI or another LangChain-supported provider.

### Q: Why Groq instead of a self-hosted model?

I used Groq because it gave fast hosted inference with a strong open-weight model through a simple API. For a prototype, that let me focus on the application architecture instead of deploying GPU infrastructure.

The tradeoff is privacy and control. A hosted provider is easier and faster to integrate, but data leaves your environment and you depend on provider availability and rate limits. Self-hosting gives more privacy and control, but requires GPU infrastructure, scaling, monitoring, and operational maturity.

For production with sensitive data, I would evaluate self-hosting, private VPC endpoints, or enterprise LLM providers with data retention guarantees.

## 7. Prompting

### Q: Show me how you structured a prompt. What was system versus user message?

I split prompts by responsibility:

```text
System message = role, rules, constraints
User message = task, data, output format
```

The system message defined the model as a restaurant menu consultant and told it not to invent, estimate, or recalculate numbers.

The user message contained the actual analytics facts, such as menu-engineering facts and top association facts, plus the required JSON output shape.

This made the prompt easier to maintain because the system rules stayed stable while the dataset facts changed per request.

### Q: Did you use few-shot examples or chain-of-thought?

I did not rely heavily on few-shot examples, and I avoided chain-of-thought. The goal was not to make the model reason creatively. The goal was to keep it grounded in computed analytics facts.

The calculations happen in Pandas, not inside the model. I used clear instructions, structured output, and precomputed facts. If recommendation quality became inconsistent, I could add few-shot examples later, but for this version the schema and constraints were enough.

### Q: Which prompt techniques did you use?

I used role prompting, grounding with facts, constraint prompting, structured output prompting, and tool-use prompting.

The model was given a restaurant consultant role, grounded in precomputed analytics facts, constrained not to invent numbers, required to return structured JSON for recommendations, and instructed to call tools for chat questions involving metrics.

## 8. RAG And Retrieval

### Q: Did you use RAG, or did you stuff data into the prompt?

I did not build a traditional RAG system in this version. There was no vector database or document retrieval. Since the source data is structured transaction data, I used deterministic analytics instead of semantic retrieval.

The backend computes menu engineering and market basket metrics, then passes compact fact summaries into the LLM. I did not send raw transaction rows to the model.

For chat, I used tools rather than RAG. The agent calls curated analytics tools to fetch relevant facts.

### Q: If asked to add a real vector database and RAG, where would it go?

I would add RAG as a separate knowledge layer between the backend and the LLM. It would not replace the Pandas analytics pipeline.

The vector database would store unstructured restaurant knowledge such as customer reviews, menu descriptions, brand guidelines, past promotion notes, supplier notes, or business rules.

The LLM would then receive both computed analytics facts and retrieved business context. Metrics like margin, quadrants, support, confidence, and lift would still be computed deterministically in code.

For tooling, I might use pgvector if I want to keep infrastructure simple with PostgreSQL, or a dedicated vector database like Pinecone, Qdrant, Weaviate, or Chroma depending on scale.

## 9. Hallucination, Correctness, And Validation

### Q: What stops the model from hallucinating a combo or pattern not in the data?

The model is not responsible for discovering combos. The backend computes item associations from actual order history using support, confidence, and lift. The LLM receives those computed facts and is instructed to use only them.

Recommendations also include supporting facts, making them auditable. In production, I would add a validator that rejects any recommendation whose cited pair or metrics do not exist in the computed analytics output.

### Q: The model recommends “put item X next to item Y.” How do you guarantee that is based on actual data?

I ground that recommendation in market basket analysis. If the model recommends placing Burger near Fries, it should be because the backend computed an association like:

```text
Burger → Fries: lift=2.40, confidence=65.0%, support=0.120
```

The backend computes those values from actual orders. The LLM only explains the finding. I would avoid saying an absolute guarantee because LLMs can still make mistakes, but the design reduces risk by requiring supporting facts and keeping calculations outside the model.

### Q: How would you know if a recommendation was actually correct?

I separate “data-supported” from “causally proven.” The app can validate that a recommendation is grounded in historical data using lift, confidence, support, units sold, and margin. But to prove it increases future sales, I would run an A/B test.

For example, one group sees the current menu, and another group sees the recommended combo or placement. I would compare average order value, revenue, margin dollars, attach rate, conversion rate, and cannibalization. If the treatment group improves significantly, then the recommendation is validated.

### Q: How would you measure whether the product actually works?

I would measure business outcomes, not just whether the AI sounds reasonable. The best approach is an A/B test comparing a control group with no recommendation applied against a treatment group where the recommendation is applied.

Metrics would include revenue, gross margin dollars, average order value, combo attach rate, units sold for promoted items, conversion rate, repeat behavior, and cannibalization. The goal is to prove the recommendation produces measurable business value.

## 10. Chat, Sessions, And Memory

### Q: Walk me through the chatbot workflow.

The user types a question in the React chat panel. The frontend sends the question and session ID to the FastAPI `/chat` endpoint. The backend uses the session ID to select the right dataset, sets that dataset as active for the request, and calls the LangChain agent.

The agent receives the user question, decides which analytics tool to call, gets precomputed facts from that tool, and then the LLM writes the final answer. The backend extracts the final AI message and returns it as JSON to the frontend.

### Q: What is the `config` argument in the agent call?

The config argument passes runtime settings to the LangChain/LangGraph agent. In this project, it sets the `thread_id` equal to the session ID.

That tells the memory system which conversation history belongs to this request. If the same session ID is used across messages, the agent can support follow-up questions like “What about its pairings?” after previously discussing an item.

### Q: Does memory send previous conversation to the LLM?

Conceptually, yes. The memory/checkpointer stores previous conversation state by session ID. When a new message comes in with the same session ID, the agent can use that previous context along with the new user message.

I do not manually concatenate chat history. LangGraph handles that through the thread ID and checkpointer.

### Q: Where is the session created?

There are two session concepts:

1. The frontend creates a normal chat session ID for demo/default chat.
2. The backend creates an upload session ID after a CSV/Excel file is successfully uploaded and parsed.

For uploaded data, the backend stores the uploaded dataset under that generated session ID and returns it to the frontend. The frontend then sends that same ID with future analytics and chat requests.

### Q: Is the session ID in all APIs different from chat session ID?

It is the same value, but it serves related purposes. For analytics endpoints, the session ID selects which dataset to analyze. For chat, the same session ID selects both the dataset and the conversation memory thread.

Using the same ID keeps the dashboard and chatbot aligned on the same uploaded dataset.

### Q: Why not have the frontend create both session IDs?

The frontend can create a basic chat session ID because it only labels a conversation. But for uploaded datasets, the backend should create the session ID because the backend owns the storage and needs to guarantee that the ID maps to a real uploaded dataset.

This avoids fake IDs, collisions, and makes future authorization easier.

### Q: Why clear the dataset binding after chat?

During a chat request, the backend temporarily attaches the current dataset to that request so internal tools use the correct data. After the request finishes, it resets that binding. This prevents stale request state from accidentally carrying into another request, especially if an error happens.

## 11. Debugging And Hard Problems

### Q: What was the hardest bug or design problem?

The hardest design problem was handling user-uploaded CSV files that had different column names and missing profitability data.

The internal analytics expected clean fields like order ID, item name, price, food cost, margin, and quantity. But real CSV exports might use names like `Order ID`, `Product`, `Price`, and `Quantity`, and they might not include `food_cost` or `margin`.

I solved this by building a normalization layer that maps flexible column names to canonical fields, validates required columns, and handles missing profitability by asking the user for an explicit assumed food-cost percentage. That kept uploads flexible without letting the AI guess margins.

### Q: Give me another real bug you solved.

After adding file upload, the frontend returned:

```text
POST http://localhost:5174/upload 404 Not Found
```

The backend route existed, so I tested the backend directly and confirmed it worked. Then I checked the frontend dev proxy and saw that `/upload` was missing from the proxy list. The request was hitting the Vite dev server instead of FastAPI. I added `/upload` to the proxy config, and the upload worked end to end.

### Q: How do you debug LLM applications?

I debug them in stages instead of treating the model as a black box. First I verify the source data. Then I check deterministic analytics outputs. Then I check the formatted facts or tool outputs sent to the model. Then I inspect the prompt and the final response. If structured output is expected, I validate the schema.

This helps identify whether the issue is in the data pipeline, analytics, model input, model behavior, or frontend rendering.

### Q: How do you unit-test a non-deterministic LLM feature?

I avoid unit-testing the model’s creativity directly. I unit-test deterministic pieces like ingestion, analytics calculations, API response shapes, tool outputs, and schema validation.

For LLM-dependent code, I mock the model and return a fake structured response. Real LLM calls are better reserved for integration or evaluation tests where I check properties like schema validity, groundedness, and absence of unsupported metrics rather than exact wording.

## 12. Cost, Latency, And Reliability

### Q: LLM calls cost money. How did you control cost?

I controlled cost by minimizing when and how the LLM is used. The LLM does not process raw transaction data or compute metrics. Pandas computes analytics locally, and the LLM receives compact summaries.

Some endpoints do not call the LLM at all, such as menu matrix, associations, upload, and health. I also rate-limited chat to reduce abuse.

The current app caches computed analytics in memory, but it does not fully cache LLM responses yet. In production, I would cache recommendation outputs by dataset hash and prompt version.

### Q: Were recommendations generated on demand or precomputed?

In the current implementation, recommendations are generated on demand when the frontend calls the menu analysis endpoint. The deterministic analytics are cached in memory, but the LLM recommendation output is not fully precomputed or cached yet.

The main latency is the LLM call. For production, I would precompute or cache recommendations after upload or data refresh, keyed by dataset version and prompt version.

### Q: What happens if the LLM API is down or slow?

The deterministic analytics still work because they do not need the LLM. Users can still see the menu matrix, associations, upload results, and health checks.

LLM-dependent features like chat and recommendation generation may fail or be slow. For production, I would add explicit timeouts, retries with exponential backoff, cached recommendations, fallback UI, and possibly a backup model provider.

### Q: What are timeouts, retries with backoff, and cached recommendations?

A timeout prevents the backend from waiting forever for the LLM. A retry tries the request again if a temporary failure occurs. Backoff waits longer between retries to avoid overwhelming the provider. Cached recommendations store the last successful output for a dataset so the app can show something useful if the LLM is temporarily unavailable.

Together, they create graceful degradation.

### Q: What happened when you hit rate limits?

The current app has basic request rate limiting around chat to reduce abuse, but it does not yet have full provider-specific rate-limit recovery. If the provider rate-limits the request, the LLM feature can fail while deterministic analytics still work.

For production, I would add retries with backoff, caching, queues for heavy AI jobs, and clear user-facing fallback messages.

## 13. Scaling

### Q: How does this hold up at 10,000 restaurants?

The current prototype would not scale as-is to 10,000 restaurants. The first thing that would break is likely in-memory session storage and on-demand LLM calls.

Uploaded data should be stored in PostgreSQL or object storage, not backend memory. Large uploads should be processed by background workers. Recommendations should be cached or precomputed so the LLM is not called every time a dashboard opens.

For scale, I would use PostgreSQL for persistent tenant data, Redis for caching, Celery or a queue system for background processing, S3 for uploaded files, and proper monitoring.

### Q: Multiple restaurants hit it at once. How did you handle concurrency?

The current app handles concurrency at a basic prototype level. FastAPI can handle concurrent requests, uploaded datasets are separated by session ID, and the in-memory session store uses a lock so concurrent uploads do not corrupt shared state.

For production, I would add authentication, tenant IDs, database-backed session storage, row-level tenant isolation, background workers for uploads, and a shared cache so the system works across multiple backend workers.

### Q: What tools would you use to scale it?

I would use PostgreSQL for persistent restaurant data, Redis for caching and session data, Celery with Redis or another queue for background jobs, S3 for uploaded files, Docker/Kubernetes or ECS for deployment, and monitoring with tools like CloudWatch, Datadog, or Prometheus.

## 14. Security And Privacy

### Q: How did you manage API keys and secrets?

I kept secrets out of the codebase by loading them from environment variables. Locally, I used a `.env` file for values like database URL and LLM API key. In production, I would use a cloud secret manager or deployment platform environment secrets, and ensure `.env` is ignored by Git.

### Q: How did you think about data security and privacy?

I treated restaurant transaction data as sensitive business data. It can reveal pricing, sales volume, and customer behavior. In the prototype, I used environment-based secrets, optional API-key authentication, rate limiting, upload size limits, session isolation, and data minimization before sending anything to the LLM.

For production, I would add real authentication, tenant-level authorization, encryption, audit logs, stricter file validation, data retention policies, and vendor review for LLM providers.

### Q: What does tenant-level authorization mean?

Tenant-level authorization means each customer or organization can only access its own data. In MenuIQ, each restaurant would be a tenant. Every API request would check that the requested uploads, analytics, recommendations, and chat history belong to that restaurant before returning data.

### Q: If this were customer financial data inside Citi, what would you add before production?

I would treat the current project as a prototype only. I would add strong identity and access control, role-based authorization, tenant checks, encryption in transit and at rest, secure secret management, audit logging, data retention controls, PII minimization, redaction before model calls, prompt injection defenses, output validation, monitoring, and human review for high-risk workflows.

I would not let the LLM directly access raw financial data or make decisions. It should summarize or explain approved deterministic outputs.

### Q: Could a user use prompt injection?

Yes, prompt injection is a real risk because the app accepts user chat input and uploaded files. A user could try to include text like “ignore previous instructions.”

The current design limits blast radius because the LLM cannot execute SQL or code and can only use curated read-only analytics tools. But for production, I would add input validation, separate trusted instructions from untrusted user data, tool allowlisting, output validation against computed facts, suspicious prompt detection, logging, and human review for high-risk actions.

### Q: If a recommendation was wrong and a restaurant lost money, who is accountable?

I would position the system as decision support, not an autonomous decision-maker. The restaurant operator remains the final decision-maker, but as the builder I am responsible for transparency, auditability, and safeguards.

I would show supporting facts, confidence indicators, warnings for assumptions, human approval, no automatic menu changes, A/B testing before broad rollout, audit logs, post-action monitoring, and rollback options.

## 15. Production Improvements

### Q: What would you improve before production?

I would add real authentication, tenant-level authorization, persistent uploaded dataset storage, stronger file validation, background processing for large uploads, LLM timeouts and retries, cached recommendations, monitoring, audit logs, secure secret management, and a proper deployment setup.

### Q: What would you add if using real customer financial data?

I would add enterprise-grade security and governance: strict access control, encryption, audit trails, model-risk review, prompt injection defenses, output validation, data minimization, approved model provider contracts, and human oversight. The LLM would only explain approved analytics outputs, not make financial decisions.

## 16. Best Short Pitch

### Q: Give me a concise interview pitch for MenuIQ.

MenuIQ is a full-stack generative AI analytics app for restaurants. It uses React on the frontend, FastAPI and PostgreSQL on the backend, and Pandas/NumPy for deterministic analytics. The system computes menu-engineering quadrants and market-basket associations from transaction data, then uses LangChain with an LLM to explain those results and produce business recommendations. The key design decision was to keep calculations outside the LLM so the recommendations are grounded, testable, and less prone to hallucination.


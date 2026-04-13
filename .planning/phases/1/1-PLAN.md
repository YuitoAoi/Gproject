# Phase 1 Plan: Backend and Frontend Infrastructure Setup

This plan outlines the executable steps to build the foundational infrastructure for both the backend and frontend, as defined in `ROADMAP.md` and guided by the decisions in `1-CONTEXT.md`.

## Part 1: Backend Setup

### Task 1.1: Initialize Python Project and Dependencies
- **Action**: Create a `backend` directory. Inside, set up a Python virtual environment (e.g., `python -m venv venv`).
- **Action**: Create a `requirements.txt` file.
- **Action**: Add the core dependencies to `requirements.txt`: `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `celery`, `redis`, `mysqlclient`, `pynvml`, `python-dotenv`, `llama-factory`.
- **Verification**: Activate the virtual environment and run `pip install -r requirements.txt`. The command must complete without any errors.

### Task 1.2: Setup FastAPI Application Structure
- **Action**: Create the main application file `backend/app/main.py`.
- **Action**: Establish a modular directory structure:
  ```
  backend/app/
  ├── api/             # Routers for different endpoints
  ├── core/            # Configuration, Celery app
  ├── db/              # Database session, models
  ├── schemas/         # Pydantic schemas
  ├── crud/            # CRUD operations
  └── services/        # Business logic (e.g., training service)
  ```
- **Action**: Implement a basic health check endpoint (`/api/v1/health`) in a new router under `backend/app/api/`.
- **Verification**: The FastAPI application starts successfully using `uvicorn app.main:app --reload`. The `/api/v1/health` endpoint returns a `200 OK` response with `{"status": "ok"}`.

### Task 1.3: Database Integration (SQLAlchemy)
- **Action**: In `backend/app/core/config.py`, manage database connection strings using environment variables.
- **Action**: In `backend/app/db/session.py`, create the SQLAlchemy engine and session management logic.
- **Action**: In `backend/app/db/models/`, define the SQLAlchemy models for `users`, `datasets`, `training_tasks`, and `models` according to the database design in `REQUIREMENTS.md`.
- **Action**: Create a script or use a migration tool (like Alembic) to create all tables in the MySQL database based on the defined models.
- **Verification**: Connect to the MySQL database and verify that all tables and their columns have been created correctly.

### Task 1.4: Celery Integration
- **Action**: In `backend/app/core/celery_app.py`, configure a Celery instance to use Redis as the message broker and result backend.
- **Action**: Create a sample task (e.g., `add(x, y)`) in a new `backend/app/tasks.py` file.
- **Action**: Create a FastAPI endpoint that triggers this sample task.
- **Verification**: Start a Celery worker. Call the FastAPI endpoint. The Celery worker logs must show the task was received and executed successfully. The task result should be retrievable via its task ID.

## Part 2: Frontend Setup

### Task 2.1: Initialize Vue Project
- **Action**: Create a `frontend` directory.
- **Action**: Use Vite to initialize a new Vue 3 project with TypeScript support: `npm create vite@latest frontend -- --template vue-ts`.
- **Action**: Navigate into the `frontend` directory and install dependencies: `npm install`.
- **Verification**: The default Vue application runs successfully on its local dev server via `npm run dev`.

### Task 2.2: Establish Project Structure & Install Core Libraries
- **Action**: Inside `frontend/src/`, create the feature-based directory structure: `api`, `assets`, `components` (for shared components), `features`, `layouts`, `router`, `store`.
- **Action**: Install necessary libraries: `npm install vue-router@4 pinia axios element-plus`.
- **Verification**: The directory structure is correctly created and all dependencies are listed in `package.json`.

### Task 2.3: Implement Application Layout
- **Action**: Create a `MainLayout.vue` component in `frontend/src/layouts/`.
- **Action**: Use Element Plus components (`el-container`, `el-header`, `el-aside`, `el-main`) to implement the 3-part layout (Top Nav, Side Menu, Content Area).
- **Action**: Create placeholder components for the header (`TheHeader.vue`) and sidebar (`TheSidebar.vue`) in `frontend/src/components/layout/`.
- **Verification**: The main layout structure is rendered correctly when `MainLayout.vue` is used as the root component in `App.vue`.

### Task 2.4: Integrate and Configure Router and State Management
- **Action**: Configure `vue-router` in `frontend/src/router/index.js`. Define a few placeholder routes (e.g., `/`, `/dashboard`, `/data-management`) that all use the `MainLayout` component.
- **Action**: Configure `pinia` in `frontend/src/main.ts` and create a simple UI store (`frontend/src/store/ui.js`) to manage the state of the sidebar (e.g., `isCollapsed`).
- **Action**: Connect the sidebar's collapse functionality to the Pinia store.
- **Verification**: Navigating to the defined routes correctly displays the corresponding placeholder page within the main layout. Clicking a button in the header correctly toggles the sidebar's collapsed state.

### Task 2.5: Create API Communication Modules
- **Action**: Create an `httpClient.js` module in `frontend/src/api/`. It should export a pre-configured `axios` instance with the backend's base URL (`http://localhost:8000/api/v1`).
- **Action**: Create a `websocket.js` module in `frontend/src/api/` with placeholder functions for `connect`, `disconnect`, and event listeners.
- **Verification**: The modules can be imported into Vue components. A test function in a component can import `httpClient` and successfully call the backend's `/health` endpoint.

## Part 3: Final Verification (UAT)

### Task 3.1: End-to-End Health Check
- **Action**: Run both the backend and frontend development servers simultaneously.
- **Action**: In the frontend, create a status indicator in the header that calls the backend's `/health` endpoint on page load.
- **Verification**: The frontend application loads in the browser, showing the full layout. The status indicator correctly shows a "Connected" state, confirming successful communication with the backend. All defined routes are navigable.

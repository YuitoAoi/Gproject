# Phase 1 Context: Frontend Architecture & Initial Setup

This document captures the key architectural decisions for the frontend of the "LLaMA-Factory 微调工作站" project, as established during the initial exploration phase. These decisions will guide the setup and implementation of Phase 1.

## 1. Project Structure

- **Decision**: The frontend project will be structured **by feature/module**.
- **Rationale**: This approach aligns with the application's clear functional divisions (Data Management, Training, Monitoring, etc.), promoting high cohesion, low coupling, and better long-term maintainability.
- **Example**:
  ```
  src/
  ├── features/
  │   ├── data-management/
  │   │   ├── components/
  │   │   ├── views/
  │   │   ├── store.js
  │   │   └── api.js
  │   └── ...
  ├── components/ (for shared/global components)
  ├── router/
  ├── store/ (for global store setup)
  ├── layouts/
  └── ...
  ```

## 2. Application Layout

- **Decision**: A classic 3-part admin layout will be implemented.
- **Components**:
    1.  **Top Navigation Bar**: For global elements like Logo, User Profile, Settings, and Notifications.
    2.  **Side Navigation Menu**: Primary navigation for switching between major feature modules. It must be collapsible.
    3.  **Main Content Area**: The workspace for displaying views and components for the selected module.

## 3. Visual & Design System

- **Decision**: A strict visual and design specification will be enforced, as detailed in `REQUIREMENTS.md`.
- **Key Points**:
    - **Color Palette**: Professional blue/gray primary tones with specific accent colors for states (success, warning, error).
    - **Typography**: Clear, sans-serif fonts (Inter, Roboto, etc.) with a defined typographic scale.
    - **Icons**: A single, consistent icon set (e.g., Material Icons).
    - **Controls**: All UI controls (buttons, inputs, etc.) will follow a unified design standard, likely based on the chosen component library (Element Plus).

## 4. State Management

- **Decision**: **Pinia** will be used for state management.
- **Implementation**:
    - Stores will be modularized, with each feature module having its own dedicated store (`/features/data-management/store.js`).
    - This aligns with the feature-based project structure and leverages Pinia's strengths in modularity and type safety.

## 5. API & Server Communication

- **Decision**: A centralized, two-pronged approach for backend communication.
- **Implementation**:
    1.  **HTTP API Client**: A dedicated module (e.g., `/src/api/client.js`) will be created, likely wrapping `axios`. It will manage base URL, authentication tokens, interceptors for request/response handling, and standardized error handling.
    2.  **WebSocket Manager**: A dedicated module (e.g., `/src/api/websocket.js`) will manage the lifecycle of WebSocket connections for real-time features (logs, metrics). It will handle connection, reconnection, and message dispatching to the relevant Pinia stores.

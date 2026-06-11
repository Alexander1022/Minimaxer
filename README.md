# Minimaxer: Optimization & Decision-Making Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Gradio](https://img.shields.io/badge/Gradio-F97316?logo=gradio&logoColor=white)](https://gradio.app/)
[![PuLP](https://img.shields.io/badge/PuLP-Optimization-blue)](https://coin-or.github.io/pulp/)
[![pytest](https://img.shields.io/badge/pytest-0A9EDC?logo=pytest&logoColor=white)](https://docs.pytest.org/)

Minimaxer is a comprehensive platform for mathematical optimization and multi-criteria decision-making. It features a robust FastAPI backend and an interactive Gradio web interface.

## 🚀 Features

### 1. Linear Programming (LP & ILP)
*   **Solver**: Powered by [PuLP](https://coin-or.github.io/pulp/) and the CBC solver.
*   **Capabilities**: Supports continuous, integer, and binary variables.
*   **Interactive Modeling**: Build, preview, and solve optimization problems in real-time.

### 2. Multi-Criteria Decision Making (MCDM)
*   **TOPSIS**: Technique for Order of Preference by Similarity to Ideal Solution. Supports hybrid criteria (Quantitative, Qualitative, Ranking).
*   **ELECTRE I**: Elimination and Choice Expressing Reality. Uses concordance and discordance indices to find the set of best alternatives (Kernel).

### 3. Modern Web Interface
*   Built with **Gradio** for a seamless user experience.
*   Dynamic alternative management and criteria configuration.
*   Mathematical model preview for verification.

---

## 🛠️ Installation & Setup

### Prerequisites
*   Python 3.10+
*   Docker & Docker Compose (optional)

### Local Development
1. **Install Dependencies**:
   ```bash
   pip install -r server/requirements.txt
   pip install -r client/requirements.txt
   ```

2. **Run the Server**:
   ```bash
   # From the project root
   uvicorn server.app.main:app --reload
   ```
   API will be available at `http://localhost:8000`. Docs at `/docs`.

3. **Run the Client**:
   ```bash
   python client/app.py
   ```
   Web interface will be available at `http://localhost:7860`.

### Running with Docker
Use the provided utility scripts:
```bash
./start.sh   # Build and start containers
./logs.sh    # View logs
./stop.sh    # Stop and remove containers
```

---

## 📖 API Usage

The backend exposes several endpoints for different solving methods under the `/api/solvers/` prefix.

| Method | Endpoint | Description |
|--------|----------|-------------|
| **Linear** | `POST /api/solvers/linear` | LP/ILP solving via PuLP |
| **TOPSIS** | `POST /api/solvers/topsis` | Multi-criteria ranking |
| **ELECTRE** | `POST /api/solvers/electre` | Outranking method (ELECTRE I) |

### Example: Linear Solver
**Request**:
```json
{
  "name": "Production_Optimization",
  "direction": "maximize",
  "variables": [
    {"name": "x", "low_bound": 0, "category": "Integer"}
  ],
  "objective": {"coefficients": {"x": 10}},
  "constraints": [
    {"coefficients": {"x": 2}, "operator": "<=", "rhs": 100}
  ]
}
```

---

## 🧪 Testing

We use `pytest` for unit and integration testing.
```bash
# Run all tests
pytest tests/ -v

# Run backend specific tests
pytest server/tests/ -v
```

---

## 📁 Project Structure

```text
├── client/          # Gradio Web Interface
│   ├── ui/          # Layout and dynamic UI components
│   └── core/        # UI logic and model builders
├── server/          # FastAPI Backend
│   └── app/         # Core application logic
│       ├── api/     # REST endpoints (Routers)
│       └── services/# Solving logic (PuLP, NumPy)
├── shared/          # Shared Pydantic schemas
└── notebooks/       # Research & prototyping
```

## 📄 License
This project is licensed under the MIT License.

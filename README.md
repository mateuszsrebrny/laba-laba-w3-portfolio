# laba-laba w3 portfolio manager

## :rocket:Overview
**laba-laba-w3-portfolio** manager is a FastAPI-powered **web3 portfolio tracker** that:
- :bank:**Records web3 transactions** with blockchain-based tracking.
- :bar_chart:**Analyzes holdings** (average buy price, portfolio summary).
- :repeat:**Supports stablecoins and derivatives** (tokens treated as equivalent with tracked conversions).
- :lock:**Has secure authentication** (public read-only, private write access).
- :test_tube:**Uses BDD tests** for reliability.

## :pushpin:Tech stack
:white_check_mark: **FastAPI Backend**  
:white_check_mark: **PostgreSQL Database** (Dockerized)  
:white_check_mark: **HTMX-Based UI** (Minimal Frontend)  
:white_check_mark: **Public Read, Private Write API** (Session & API Key Auth)  
:white_check_mark: **BDD Tests** (Login, Transactions, Token Management)  
:white_check_mark: **Automated Deployment** (via Render)

---

## :wrench:**Installation & Setup**
### **:one: Clone the Repository**
```sh
git clone https://github.com/mateuszsrebrny/laba-laba-w3-portfolio.git
cd laba-laba-w3-portfolio
```

### **:two: Set Up Environment Variables**
:pushpin:**Create a `.env` file**:
```ini
DATABASE_URL=postgresql://pi_user:your_password@postgres/ll-w3-dev
API_KEY=your_secret_api_key
SECRET_KEY=your_secret_session_key

USERNAME=admin
PASSWORD=your_secure_password

TEST_USERNAME=test_user
TEST_PASSWORD=test_password
TEST_MODE=false
```

### **:three: Run the Application with Docker**
```sh
docker compose up --build
```

### **:four: Run BDD Tests**
```sh
docker compose run test
```

---

## :pickaxe: Useful dev commands

### Start the app

```bash 
docker compose up --build -d
```

### Check the logs 

```bash
docker logs laba-laba-dev-app -f
```

### Stop the app

Without cleaning db volume:
```bash
docker compose down
```

With cleaning db volume:
```bash
docker compose down -v
```

### Select from the db

```bash
docker exec -it laba-laba-dev-db psql -U ll_dev_user -d laba_laba_dev -c "select * from transactions;"
```

---

## :rocket:**API Documentation**
The API provides **Swagger UI** and **ReDoc** for documentation.

- :book:**Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)  
- :book:**ReDoc UI:** [http://localhost:8000/redoc](http://localhost:8000/redoc)  


---

## :scroll:**License**
Licensed under the [MIT License](https://opensource.org/licenses/MIT).  

---
:rocket:**Built with :heart: by [mateuszsrebrny](https://github.com/mateuszsrebrny)**


from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
from pydantic import BaseModel
from typing import Optional

app = FastAPI()
port = 3002

# Enable CORS for all routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create or open the SQLite database
try:
    conn = sqlite3.connect("users.db", check_same_thread=False)
    cursor = conn.cursor()
    print("Database opened successfully.")
except Exception as e:
    print("Error opening the database:", e)

# Create the Users table if it doesn't exist
createUsersTableQuery = """
  CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
  );
"""
try:
    cursor.execute(createUsersTableQuery)
    conn.commit()
    print("Users table created successfully.")
except Exception as e:
    print("Error creating Users table:", e)

# Create the Agents table if it doesn't exist
createAgentTableQuery = """
  CREATE TABLE IF NOT EXISTS Agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    prompt TEXT NOT NULL,
    context TEXT,
    logo_url TEXT
  );
"""
try:
    cursor.execute(createAgentTableQuery)
    conn.commit()
    print("Agents table created successfully.")
except Exception as e:
    print("Error creating Agents table:", e)

# Pydantic models for request bodies
class SignupData(BaseModel):
    username: str
    email: str
    password: str

class SigninData(BaseModel):
    username: str
    password: str

class AgentData(BaseModel):
    username: str
    agent_name: str
    prompt: str
    context: Optional[str] = None
    logo_url: Optional[str] = None

class UpdateAgentData(BaseModel):
    username: str
    agent_name: str
    prompt: Optional[str] = None
    context: Optional[str] = None
    logo_url: Optional[str] = None

class DeleteAgentData(BaseModel):
    username: str
    agent_name: str

# Sign Up API
@app.post("/signup")
def signup(data: SignupData):
    if not data.username or not data.email or not data.password:
        raise HTTPException(status_code=400, detail="All fields are required")
    
    insertQuery = """
      INSERT INTO Users (username, email, password)
      VALUES (?, ?, ?);
    """
    try:
        cursor.execute(insertQuery, (data.username, data.email, data.password))
        conn.commit()
        user_id = cursor.lastrowid
        return {"message": "User created successfully", "userId": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to sign up user")

# Sign In API
@app.post("/signin")
def signin(data: SigninData):
    if not data.username or not data.password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    
    query = "SELECT * FROM Users WHERE username = ?"
    cursor.execute(query, (data.username,))
    row = cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    
    # row: (id, username, email, password)
    if row[3] == data.password:
        user = {"id": row[0], "username": row[1], "email": row[2], "password": row[3]}
        return {"message": "Login successful", "user": user}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# Get all signed up users API
@app.get("/users")
def get_users():
    query = "SELECT id, username, email FROM Users"
    cursor.execute(query)
    rows = cursor.fetchall()
    users = [{"id": row[0], "username": row[1], "email": row[2]} for row in rows]
    return {"users": users}

# Create a new agent API
@app.post("/agents")
def create_agent(data: AgentData):
    if not data.username or not data.agent_name or not data.prompt:
        raise HTTPException(status_code=400, detail="Username, agent_name, and prompt are required")
    
    insertQuery = """
      INSERT INTO Agents (username, agent_name, prompt, context, logo_url)
      VALUES (?, ?, ?, ?, ?);
    """
    try:
        cursor.execute(insertQuery, (data.username, data.agent_name, data.prompt, data.context, data.logo_url))
        conn.commit()
        agent_id = cursor.lastrowid
        return {"message": "Agent created successfully", "agentId": agent_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create agent")

# Get all agents API
@app.get("/agents")
def get_agents():
    query = "SELECT id, username, agent_name, prompt, context, logo_url FROM Agents"
    cursor.execute(query)
    rows = cursor.fetchall()
    agents = []
    for row in rows:
        agents.append({
            "id": row[0],
            "username": row[1],
            "agent_name": row[2],
            "prompt": row[3],
            "context": row[4],
            "logo_url": row[5]
        })
    return {"agents": agents}

# Get User Keys API (/api/user-keys)
@app.get("/api/user-keys")
def get_user_keys(username: str = Query(...)):
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    
    query = "SELECT agent_name, prompt, context, logo_url FROM Agents WHERE username = ?"
    cursor.execute(query, (username,))
    rows = cursor.fetchall()
    
    if len(rows) == 0:
        raise HTTPException(status_code=404, detail="No agents found for this user")
    
    userKeys = {}
    for row in rows:
        userKeys[row[0]] = {
            "prompt": row[1],
            "context": row[2],
            "logo_url": row[3]
        }
    return userKeys

# Create User Key API (/api/user-keys)
@app.post("/api/user-keys")
def create_user_key(data: AgentData):
    if not data.username or not data.agent_name or not data.prompt:
        raise HTTPException(status_code=400, detail="Username, agent_name, and prompt are required")
    
    insertQuery = """
      INSERT INTO Agents (username, agent_name, prompt, context, logo_url)
      VALUES (?, ?, ?, ?, ?);
    """
    try:
        cursor.execute(insertQuery, (data.username, data.agent_name, data.prompt, data.context, data.logo_url))
        conn.commit()
        agent_id = cursor.lastrowid
        return {"message": "Agent created successfully", "agentId": agent_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create agent")

# Delete User Key API (/api/user-keys)
@app.delete("/api/user-keys")
def delete_user_key(data: DeleteAgentData):
    if not data.username or not data.agent_name:
        raise HTTPException(status_code=400, detail="Username and agent_name are required")
    
    deleteQuery = """
      DELETE FROM Agents WHERE username = ? AND agent_name = ?;
    """
    try:
        cursor.execute(deleteQuery, (data.username, data.agent_name))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Agent not found")
        return {"message": "Agent deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete agent")

# Update User Key API (/api/user-keys)
@app.put("/api/user-keys")
def update_user_key(data: UpdateAgentData):
    if not data.username or not data.agent_name:
        raise HTTPException(status_code=400, detail="Username and agent_name are required")
    
    updateFields = []
    updateValues = []
    if data.prompt is not None:
        updateFields.append("prompt = ?")
        updateValues.append(data.prompt)
    if data.context is not None:
        updateFields.append("context = ?")
        updateValues.append(data.context)
    if data.logo_url is not None:
        updateFields.append("logo_url = ?")
        updateValues.append(data.logo_url)
    
    if len(updateFields) == 0:
        raise HTTPException(
            status_code=400,
            detail="At least one field (prompt, context, logo_url) must be provided to update"
        )
    
    updateQuery = f"""
      UPDATE Agents
      SET {', '.join(updateFields)}
      WHERE username = ? AND agent_name = ?;
    """
    try:
        cursor.execute(updateQuery, (*updateValues, data.username, data.agent_name))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Agent not found")
        return {"message": "Agent updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update agent")

# Start the server (use: uvicorn filename:app --port 3002)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

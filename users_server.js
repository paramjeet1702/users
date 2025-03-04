const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const app = express();
const port = 3002;

const cors = require("cors");

// Enable CORS for all routes
app.use(cors());
// Middleware to parse JSON bodies
app.use(express.json());

// Create or open the SQLite database
const users_db = new sqlite3.Database('users.db', (err) => {
  if (err) {
    console.error('Error opening the database:', err);
  } else {
    console.log('Database opened successfully.');
  }
});

// Create the Users table if it doesn't exist
const createUsersTableQuery = `
  CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
  );
`;

users_db.run(createUsersTableQuery, (err) => {
  if (err) {
    console.error('Error creating Users table:', err);
  } else {
    console.log('Users table created successfully.');
  }
});

// Create the Agents table if it doesn't exist
const createAgentTableQuery = `
  CREATE TABLE IF NOT EXISTS Agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    prompt TEXT NOT NULL,
    context TEXT,
    logo_url TEXT
  );
`;

users_db.run(createAgentTableQuery, (err) => {
  if (err) {
    console.error('Error creating Agents table:', err);
  } else {
    console.log('Agents table created successfully.');
  }
});

// Sign Up API
app.post('/signup', (req, res) => {
  const { username, email, password } = req.body;

  if (!username || !email || !password) {
    return res.status(400).json({ error: 'All fields are required' });
  }

  const insertQuery = `
    INSERT INTO Users (username, email, password)
    VALUES (?, ?, ?);
  `;

  users_db.run(insertQuery, [username, email, password], function (err) {
    if (err) {
      return res.status(500).json({ error: 'Failed to sign up user' });
    }
    res.status(201).json({ message: 'User created successfully', userId: this.lastID });
  });
});

// Sign In API
app.post("/signin", (req, res) => {
  const { username, password } = req.body;

  if (!username || !password) {
    return res.status(400).json({ message: "Username and password are required" });
  }

  const query = `SELECT * FROM Users WHERE username = ?`;

  users_db.get(query, [username], (err, row) => {
    if (err) {
      return res.status(500).json({ message: "Server error" });
    }

    if (!row) {
      return res.status(404).json({ message: "User not found" });
    }

    if (row.password === password) {
      res.status(200).json({ message: "Login successful", user: row });
    } else {
      res.status(401).json({ message: "Invalid credentials" });
    }
  });
});

// Get all signed up users API
app.get('/users', (req, res) => {
  const query = 'SELECT id, username, email FROM Users'; // Select only the necessary fields
  
  users_db.all(query, [], (err, rows) => {
    if (err) {
      return res.status(500).json({ error: 'Failed to retrieve users' });
    }

    res.status(200).json({ users: rows });
  });
});

// Create a new agent API
app.post('/agents', (req, res) => {
  const { username, agent_name, prompt, context, logo_url } = req.body;

  if (!username || !agent_name || !prompt) {
    return res.status(400).json({ error: 'Username, agent_name, and prompt are required' });
  }

  const insertQuery = `
    INSERT INTO Agents (username, agent_name, prompt, context, logo_url)
    VALUES (?, ?, ?, ?, ?);
  `;

  users_db.run(insertQuery, [username, agent_name, prompt, context, logo_url], function (err) {
    if (err) {
      return res.status(500).json({ error: 'Failed to create agent' });
    }
    res.status(201).json({ message: 'Agent created successfully', agentId: this.lastID });
  });
});

// Get all agents API
app.get('/agents', (req, res) => {
  const query = 'SELECT id, username, agent_name, prompt, context, logo_url FROM Agents';
  
  users_db.all(query, [], (err, rows) => {
    if (err) {
      return res.status(500).json({ error: 'Failed to retrieve agents' });
    }

    res.status(200).json({ agents: rows });
  });
});

// Get User Keys API (/api/user-keys)
app.get('/api/user-keys', (req, res) => {
  const { username } = req.query;

  if (!username) {
    return res.status(400).json({ error: 'Username is required' });
  }

  const query = 'SELECT agent_name, prompt, context, logo_url FROM Agents WHERE username = ?';

  users_db.all(query, [username], (err, rows) => {
    if (err) {
      return res.status(500).json({ error: 'Failed to retrieve user data' });
    }

    if (rows.length === 0) {
      return res.status(404).json({ error: 'No agents found for this user' });
    }

    const userKeys = {};

    rows.forEach(row => {
      userKeys[row.agent_name] = {
        prompt: row.prompt,
        context: row.context,
        logo_url: row.logo_url
      };
    });

    res.status(200).json(userKeys);
  });
});

// Create User Key API (/api/user-keys)
app.post('/api/user-keys', (req, res) => {
  const { username, agent_name, prompt, context, logo_url } = req.body;

  if (!username || !agent_name || !prompt) {
    return res.status(400).json({ error: 'Username, agent_name, and prompt are required' });
  }

  const insertQuery = `
    INSERT INTO Agents (username, agent_name, prompt, context, logo_url)
    VALUES (?, ?, ?, ?, ?);
  `;

  users_db.run(insertQuery, [username, agent_name, prompt, context, logo_url], function (err) {
    if (err) {
      return res.status(500).json({ error: 'Failed to create agent' });
    }
    res.status(201).json({ message: 'Agent created successfully', agentId: this.lastID });
  });
});

// Delete User Key API (/api/user-keys)
app.delete('/api/user-keys', (req, res) => {
  const { username, agent_name } = req.body;

  if (!username || !agent_name) {
    return res.status(400).json({ error: 'Username and agent_name are required' });
  }

  const deleteQuery = `
    DELETE FROM Agents WHERE username = ? AND agent_name = ?;
  `;

  users_db.run(deleteQuery, [username, agent_name], function (err) {
    if (err) {
      return res.status(500).json({ error: 'Failed to delete agent' });
    }

    if (this.changes === 0) {
      return res.status(404).json({ error: 'Agent not found' });
    }

    res.status(200).json({ message: 'Agent deleted successfully' });
  });
});

// Update User Key API (/api/user-keys) - New API to update agent details
app.put('/api/user-keys', (req, res) => {
    const { username, agent_name, prompt, context, logo_url } = req.body;
  
    if (!username || !agent_name) {
      return res.status(400).json({ error: 'Username and agent_name are required' });
    }
  
    // Build dynamic SQL query for the update
    let updateFields = [];
    let updateValues = [];
  
    if (prompt) {
      updateFields.push("prompt = ?");
      updateValues.push(prompt);
    }
  
    if (context) {
      updateFields.push("context = ?");
      updateValues.push(context);
    }
  
    if (logo_url) {
      updateFields.push("logo_url = ?");
      updateValues.push(logo_url);
    }
  
    if (updateFields.length === 0) {
      return res.status(400).json({ error: 'At least one field (prompt, context, logo_url) must be provided to update' });
    }
  
    const updateQuery = `
      UPDATE Agents
      SET ${updateFields.join(", ")}
      WHERE username = ? AND agent_name = ?;
    `;
  
    users_db.run(updateQuery, [...updateValues, username, agent_name], function (err) {
      if (err) {
        return res.status(500).json({ error: 'Failed to update agent' });
      }
  
      if (this.changes === 0) {
        return res.status(404).json({ error: 'Agent not found' });
      }
  
      res.status(200).json({ message: 'Agent updated successfully' });
    });
  });
  
  // Start the server
  app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
  });

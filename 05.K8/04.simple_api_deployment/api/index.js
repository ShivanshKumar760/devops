import express from "express";

const app = express();
const port = 3000;

const db = [{ id: 1, name: "Alice", age: 30 }];

app.use(express.json());

app.get("/", (req, res) => {
  res.send("Welcome to the User API!");
});

app.get("/users", (req, res) => {
  res.json(db);
});

app.get("/user/:id", (req, res) => {
  const { id } = req.params;
  const parsedId = parseInt(id, 10);
  if (isNaN(parsedId)) {
    return res.status(400).json({ error: "Invalid user ID" });
  }

  const user = db.find(function (user) {
    if (user.id === parsedId) {
      return true;
    }
  });

  if (user) {
    res.json(user);
  } else {
    res.status(404).json({ error: "User not found" });
  }
});

app.post("/user", (req, res) => {
  const { name, age } = req.body;
  if (!name || !age) {
    return res.status(400).json({ error: "Name and age are required" });
  }

  const lengthOfDb = db.length;
  let fetchLastIndex = db[lengthOfDb - 1].id;
  const newUser = {
    id: fetchLastIndex + 1,
    name,
    age,
  };
  db.push(newUser);
  res.status(201).json(newUser);
});

app.put("/user/:id", (req, res) => {
  const { id } = req.params;
  const parsedId = parseInt(id, 10);
  if (isNaN(parsedId)) {
    return res.status(400).json({ error: "Invalid user ID" });
  }

  const userIndex = db.findIndex(function (user) {
    if (user.id === parsedId) {
      return true;
    }
  });

  if (userIndex !== -1) {
    const { name, age } = req.body;
    if (!name || !age) {
      return res.status(400).json({ error: "Name and age are required" });
    }
    db[userIndex] = { id: parsedId, name, age };
    res.json(db[userIndex]);
  }
});

app.patch("/user/:id", (req, res) => {
  const { id } = req.params;
  const parsedId = parseInt(id, 10);

  const user = db.find(function (user) {
    if (user.id === parsedId) {
      return true;
    }
  });

  if (user) {
    const { name, age } = req.body;
    if (name) {
      user.name = name;
    }
    if (age) {
      user.age = age;
    }
    res.json(user);
  } else {
    res.status(404).json({ error: "User not found" });
  }

  //or

  //   const userIndex = db.findIndex(function (user) {
  //     if (user.id === parsedId) {
  //       return true;
  //     }
  //   });
  //   if (userIndex !== -1) {
  //     const { name, age } = req.body;
  //     if (name) {
  //       db[userIndex].name = name;
  //     }
  //     if (age) {
  //       db[userIndex].age = age;
  //     }
  //     res.json(db[userIndex]);
  //   } else {
  //     res.status(404).json({ error: "User not found" });
  //   }
});

app.delete("/user/:id", (req, res) => {
  const { id } = req.params;
  const parsedId = parseInt(id, 10);
  if (isNaN(parsedId)) {
    return res.status(400).json({ error: "Invalid user ID" });
  }

  const userIndex = db.findIndex(function (user) {
    if (user.id === parsedId) {
      return true;
    }
  });

  if (userIndex !== -1) {
    db.splice(userIndex, 1);
    res.json({ message: "User deleted successfully" });
  } else {
    res.status(404).json({ error: "User not found" });
  }
});

app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});

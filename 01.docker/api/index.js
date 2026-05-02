import express from "express";
import mongoose from "mongoose";
import cors from "cors";
import jwt from "jsonwebtoken";
import bcrypt from "bcryptjs";

const app = express();

const UserSchema = new mongoose.Schema({
  username: { type: String, required: true, unique: true },
  password: {
    type: String,
    required: true,
    unique: true,
  },
});

const DockerUser = mongoose.model("DockerUser", UserSchema);

const TodoSchema = new mongoose.Schema({
  title: { type: String, required: true },
  description: { type: String, required: true },
  userId: { type: mongoose.Schema.Types.ObjectId, ref: "DockerUser" },
});

const DockerTodo = mongoose.model("DockerTodo", TodoSchema);

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

const PORT = 3000;

const authMiddleware = async (req, res, next) => {
  const token = req.headers.authorization?.split(" ")[1];
  if (!token) {
    return res.status(401).json({ msg: "No token provided" });
  }
  try {
    const decoded = jwt.verify(token, "secretkey");
    req.user = decoded;
    next();
  } catch (err) {
    return res.status(401).json({ msg: "Invalid token" });
  }
};

//User registration service

const register = (req, res) => {
  const { username, password } = req.body;
  if (!username || !password) {
    return res
      .status(400)
      .json({ msg: "Please provide username and password" });
  }
  const hashedPasswordSync = bcrypt.hashSync(password, 10);
  DockerUser.create({ username, password: hashedPasswordSync })
    .then((user) => {
      res.status(201).json({ msg: "User registered successfully", user });
    })
    .catch((err) => {
      console.log(err);
      res
        .status(500)
        .json({ msg: "Error registering user", error: err.message });
    });
};

//User login service via async and await
const login = async (req, res) => {
  const { username, password } = req.body;
  const User = await DockerUser.findOne({ username });
  console.log("User:", User);
  if (!User) {
    return res
      .status(404)
      .json({ msg: `No such user with username: ${username}.` });
  }

  //check password matching
  const isMatched = await bcrypt.compare(password, User.password);
  if (!isMatched) {
    return res.status(401).json({ msg: "Invalid password" });
  }
  //generate JWT token
  const token = jwt.sign(
    { id: User._id, username: User.username },
    "secretkey",
    { expiresIn: "1h" }
  );
  return res.status(200).json({ msg: "Login successful", token });
};

app.post("/register", register);
app.post("/login", login);

//Todo CRUD operations
const createTodo = async (req, res) => {
  const { title, description } = req.body;
  const userId = req.user._id;
  if (!title || !description) {
    return res
      .status(400)
      .json({ msg: "Please provide title and description" });
  }
  //via save method
  //const newTodo = new DockerTodo({ title, description, userId });
  //await newTodo.save(); //save is a sync or async method?
  //without await, it will return a promise that resolves to the saved document, but we want to wait for the save operation to complete before sending the response.
  //answer is :save is an async method, it returns a promise that resolves to the saved document.
  /*
    DockerTodo.create({title, description, userId})
    .then((todo)=>{
        res.status(201).json({msg:"Todo created successfully", todo});
    })

    newTodo.save().then((todo)=>{
        res.status(201).json({msg:"Todo created successfully", todo});
    })

    */

  const todo = await DockerTodo.create({ title, description, userId });
  res.status(201).json({ msg: "Todo created successfully", todo });
};

const getAllTodos = async (req, res) => {
  const userId = req.user._id;
  const todos = await DockerTodo.find({ userId });
  res.status(200).json({ msg: "Todos retrieved successfully", todos });
};

app.post("/todos", authMiddleware, createTodo);
app.get("/todos", authMiddleware, getAllTodos);

mongoose.connect("mongodb://localhost:27017/docker-todo-app").then(() => {
  console.log("Connected to MongoDB");
  app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
  });
});

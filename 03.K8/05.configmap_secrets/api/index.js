import express from "express";
import dotenv from "dotenv";
dotenv.config();
const app = express();
const port = 3000;

app.use(express.json());

app.get("/", (req, res) => {
  const normalMessage = process.env.NORMAL_ENV_VALUE;
  res.send(`Welcome User,to the ${normalMessage} `);
});

app.get("/secret", (req, res) => {
  const secretMessage = process.env.SECRET_ENV_VALUE;
  res.send(`Welcome User,to the ${secretMessage} `);
});

app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});

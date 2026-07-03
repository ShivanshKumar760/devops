import express from "express";
import bcrypt from "bcrypt";
import pool from "./db/db.js";
import { createToken,tokenRequired } from "./middleware/auth.js";
import cors from "cors";

const app = express();
app.use(express.json());
app.use(cors());
process.on("unhandledRejection",(reason,promise)=>{
    console.error("❌ CRITICAL:Unhandled Rejection at:",promise," reason:",reason);
});

process.on("uncaughtException",(err)=>{
    console.error("❌ Critical:Uncaught exception thrown:",err);
});

let latestEvent = {
    version:0,
    type:null,
    data:null
};

function publishEvent(eventType,data){
    latestEvent.version+=1;
    latestEvent.type=eventType;
    latestEvent.data=data;

}

function sleep(ms){
    return new Promise((resolve)=>{
        return setTimeout(resolve,ms)
    })
}

async function waitForNewEvent(sinceVersion, timeoutMs = 25000) {
    const start = Date.now();
    
    // 1. FIXED: Changed Data.now() to Date.now()
    while (Date.now() - start < timeoutMs) {
        if (latestEvent.version > sinceVersion) {
            return { ...latestEvent }; // shallow copy
        }

        // 2. FIXED: Wrapped inside the loop properly to pause for 500ms
        await sleep(500);
    }
    return null;
}


// ----Auth routes ------

app.post("/signup",async (req,res)=>{
    const {username,email,password}=req.body;
    if(!username || !email || !password){
        return res.status(400).json({error:"Username , email and password are required."})
    }

    const passwordHash = await bcrypt.hash(password,10);

    try {
        const result = await pool.query(`INSERT INTO USERS (username,email,password_hash) VALUES ($1,$2,$3)
            RETURNING user_id , username , email`,[username,email,passwordHash]);
        const user = result.rows[0];
        const token = createToken(user.user_id);
        return res.status(201).json({user,token});
    } catch (error) {
        if(err.code==="23505"){
            return res.status(409).json({error:"username or email already taken"});
        }
        console.log(error);
        return res.status(500).json({error:"Internal Server error"});
    }
});


app.post("/login",async (req,res)=>{
    const {username , password} = req.body;
    const result = await pool.query(`SELECT * FROM users WHERE username = $1 `,[username]);
    const user = result.rows[0];
    if(!user || ! (await bcrypt.compare(password,user.password_hash))){
        return res.status(401).json({error:"Invalid username or password"});
    }
    const token = createToken(user.user_id);
    return res.status(200).json({token});
});

// ----- Profile routes -------
app.get("/users/:userId",async (req,res)=>{
    const userId = parseInt(req.params.userId,10);
    const result = await pool.query(`SELECT user_id,username,email,bio,created_at FROM users WHERE user_id = $1`,[userId]);

    const user = result.rows[0];
    if(!user){
        return res.status(404).json({error:"User not found"});
    }
    return res.status(200).json(user);
});

app.put("/users/me",tokenRequired,async (req,res)=>{
    const {bio} = req.body;

    const result = await pool.query(
        `UPDATE users SET bio = $1 WHERE user_id = $2 RETURNING user_id,username,bio`,[bio,req.userId]
    );

    return res.status(200).json(result.rows[0]);
});

// ---- Post routes -----
app.post("/posts",tokenRequired,async (req,res)=>{
    const {caption,image_url} = req.body;
    if (!image_url){
        return res.status(400).json({error:"image_url is required"});
    }

    const result = await pool.query(
        `INSERT INTO posts (user_id,caption,image_url)
        VALUES ($1,$2,$3)
        RETURNING post_id,user_id,caption,image_url,created_at
        `,[req.userId,caption,image_url]
    );

    const post = result.rows[0];
    publishEvent("new_post",post);
    return res.status(201).json(post);
});

app.get("/feed",async (req,res)=>{
    const limit = parseInt(req.query.limit || "10",10);
    const offset = parseInt(req.query.offset || "0",10);

    const result = await pool.query(
        `SELECT posts.post_id, posts.caption, posts.image_url, posts.created_at,
            users.username,
            COUNT(likes.user_id) AS like_count
     FROM posts
     JOIN users ON posts.user_id = users.user_id
     LEFT JOIN likes ON posts.post_id = likes.post_id
     GROUP BY posts.post_id, posts.caption, posts.image_url, posts.created_at, users.username
     ORDER BY posts.created_at DESC
     LIMIT $1 OFFSET $2`,[limit, offset]
    );

    return res.status(200).json(result.rows);
})

// ---- like routes -------
app.post("/posts/:postId/like",tokenRequired , async (req,res)=>{
    const postId = parseInt(req.params.postId,10);
    try{
        await pool.query("INSERT INTO likes (user_id,post_id) VALUES ($1,$2)",[req.userId,postId]);
    }catch(err){
        if (err.code==="23505"){
            return res.status(409).json({error:"Already Liked"});
        }
        console.error(err);
        return res.status(500).json({error:"Internal Server error"});
    }

    const countResult=await pool.query(`SELECT COUNT(*) FROM likes WHERE post_id = $1`,[postId]);
    const likeCount = parseInt(countResult.rows[0].count,10);
    publishEvent("new_like",{post_id:postId,like_count:likeCount});
    return res.status(201).json({
        post_id:postId,like_count:likeCount
    });
})

app.delete("/posts/:postId/like", tokenRequired, async (req, res) => {
  const postId = parseInt(req.params.postId, 10);

  await pool.query("DELETE FROM likes WHERE user_id = $1 AND post_id = $2", [
    req.userId,
    postId,
  ]);

  const countResult = await pool.query(
    "SELECT COUNT(*) FROM likes WHERE post_id = $1",
    [postId]
  );
  const likeCount = parseInt(countResult.rows[0].count, 10);

  publishEvent("unlike", { post_id: postId, like_count: likeCount });
  return res.status(200).json({ post_id: postId, like_count: likeCount });
});

// ---------- Long polling endpoint ----------

app.get("/events/poll", async (req, res) => {
  const sinceVersion = parseInt(req.query.since || "0", 10);
  const event = await waitForNewEvent(sinceVersion);

  if (event === null) {
    return res.status(204).json({ timeout: true, version: sinceVersion });
  }
  return res.status(200).json(event);
});

try {
  await pool.query("SELECT 1");
  console.log("Database connected");
} catch (err) {
  console.error(err);
}
const PORT = 5001;

const server = app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});

console.log(server.listening);

process.on("exit", (code) => {
  console.log("EXIT:", code);
});

server.on("close", () => {
  console.log("SERVER CLOSED");
});
import jwt from "jsonwebtoken";
import dotenv from "dotenv";

dotenv.config();

const SECRET_KEY = process.env.SECRET_KEY;

function createToken(userId){
    return jwt.sign({
        user_id:userId
    },SECRET_KEY,{expiresIn:"7d"});
}


function tokenRequired(req, res, next){
    const authHeader=req.headers["authorization"]||""
    if(!authHeader.startsWith("Bearer ")){
        return res.status(401).json({
            error:"Missing or malformed Authorization header"
        });
    }

    const token=authHeader.split(" ")[1];
    try{
        const payload=jwt.verify(token,SECRET_KEY);
        req.userId=payload.user_id
        next()
    }
    catch(err){
        if(err.name==="TokenExpiredError"){
            return res.status(401).json({error:"Token expired"});
        }

        return res.status(401).json({ error: "Invalid token" });
    }
}

export {
    createToken,
    tokenRequired
}
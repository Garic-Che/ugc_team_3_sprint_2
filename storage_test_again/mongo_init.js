db.createCollection("users")
db.createCollection("movies")

db.users.createIndex({ "username": 1 }, { 
    unique: true,
    name: "users_username_idx",
    background: true,
    collation: { locale: "en", strength: 2 }
})

db.movies.createIndex({ "title": 1 }, { 
    unique: true,
    name: "movies_title_idx",
    background: true,
    collation: { locale: "en", strength: 2 }
})

db.movies.createIndex({ "likes_count": 1 }, { name: "movies_likes_idx" })
db.users.createIndex({ "likes": 1 }, { name: "users_likes_idx" })

db.users.createIndex({ "likes": 1 }, { 
    name: "users_likes_idx",
    background: true
});

db.movies.createIndex({ 
    "_id": 1, 
    "likes_count": 1 
}, { name: "movies_id_likes" });

db.setProfilingLevel(1, {slowms: 50})
db = new Mongo().getDB("ugc")

db.Like.insertMany([
    {
        _id: UUID("3f8a5e78-2c5b-4b3d-9f9e-882a74e0c4e1"),
        user_id: UUID("476bff82-92d5-4c21-99ef-67cbbdd5fd5e"), 
        content_id: UUID("2a7d84a6-befe-437d-8813-e6d5bb06a34f"), 
        created_at: new Date("2021-01-01T10:00:00"),
        rate: 5,
    },
    {
        _id: UUID("84e2b9c1-3d47-4a6c-b1f3-75e9d4a6f9c2"),
        user_id: UUID("476bff82-92d5-4c21-99ef-67cbbdd5fd5e"), 
        content_id: UUID("a7f12e4b-5c8d-40e9-821e-9d2b3478f1a5"), 
        created_at: new Date("2021-01-02T10:00:00"),
        rate: 10,
    },
    {
        _id: UUID("e7d294b1-5a3f-41c8-92f8-37f3b6d48c8e"),
        user_id: UUID("550e8400-e29b-41d4-a716-446655440000"), 
        content_id: UUID("c9d4c530-7657-4ca3-bc8d-0b888e65000b"), 
        created_at: new Date("2021-01-01T11:00:00"),
        rate: 10,
    },
    {
        _id: UUID("2ad262f4-442a-490e-bb1a-6d3b94d132ef"),
        user_id: UUID("476bff82-92d5-4c21-99ef-67cbbdd5fd5e"), 
        content_id: UUID("c9d4c530-7657-4ca3-bc8d-0b888e65000b"), 
        created_at: new Date("2021-01-01T11:00:00"),
        rate: 5,
    },
]);

db.Bookmark.insertMany([
    {
        _id: UUID("f9a63c7e-d0bf-47b2-b821-3d2a74185a2d"),
        user_id: UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479"), 
        content_id: UUID("6fa459ea-ee8a-3ca4-894e-db77e160355e"), 
        created_at: new Date("2021-01-01T10:00:00"),
    },
    {
        _id: UUID("6bfa7d2a-e1c0-47b9-91d5-23a6075fbac2"),
        user_id: UUID("9f8d08af-72cd-4c85-8d29-7b28f4d3f48d"), 
        content_id: UUID("8148f77d-a44b-48d3-9df5-0f8b1a53fd2b"), 
        created_at: new Date("2021-01-01T11:00:00"),
    },
    {
        _id: UUID("d3a17b85-6f2d-4b7f-9e23-1c4f78e2a5d6"),
        user_id: UUID("f85c4a92-1b3d-45c7-8d7e-62a174b9e3f2"), 
        content_id: UUID("8148f77d-a44b-48d3-9df5-0f8b1a53fd2b"), 
        created_at: new Date("2021-01-02T12:00:00"),
    },
]);

db.Comment.insertMany([
    {
        _id: UUID("12d4c8f9-82a1-4d61-b964-5298d9f321b3"),
        user_id: UUID("7f5198c6-1545-4b3e-b865-4a652f87e5dd"),
        content_id: UUID("2ad262f4-442a-490e-bb1a-6d3b94d132ef"),
        created_at: new Date("2025-05-08T19:10:00"),
        text: "your state proud of words",
    },
    {
        _id: UUID("bfc3a687-8f4d-46b5-b3e9-81c2b760bf2d"),
        user_id: UUID("48d6e3e1-d19a-4aad-af8a-2c5a95831397"),
        content_id: UUID("1b459e76-fc8d-4eb6-b5cc-23e73c732af7"),
        created_at: new Date("2025-05-09T10:55:00"),
        text: "some random words put into sentence",
    }
]);
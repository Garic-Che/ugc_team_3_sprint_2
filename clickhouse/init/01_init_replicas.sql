CREATE DATABASE shard;

CREATE TABLE shard.clicks (
    id UUID,
    event_time DateTime64(3, 'UTC'),
    user_id UUID,
    page_url String,
    content_type Enum16('film', 'trailer', 'settings', 'search') 
) ENGINE = ReplicatedMergeTree('/clickhouse/tables/{shard}/test', '{replica}') 
PARTITION BY toYYYYMMDD(event_time) 
ORDER BY (content_type, event_time);

CREATE TABLE shard.visits (
    id UUID,
    user_id UUID,
    page_url String,
    page_type Enum16('film', 'account', 'settings', 'finance'),
    started_at DateTime64(3, 'UTC'),
    finished_at DateTime64(3, 'UTC'),
) ENGINE = ReplicatedMergeTree('/clickhouse/tables/{shard}/visits', '{replica}') 
PARTITION BY toYYYYMMDD(started_at) 
ORDER BY page_type;

CREATE TABLE shard.resolution_changes (
    id UUID,
    event_time DateTime64(3, 'UTC'),
    user_id UUID,
    video_id UInt32,
    target_resolution Enum8('480', '720', '1080', '1440', '4K', '8K'),
    origin_resolution Enum8('480', '720', '1080', '1440', '4K', '8K')
) ENGINE = ReplicatedMergeTree('/clickhouse/tables/{shard}/resolution_changes', '{replica}') 
PARTITION BY toYYYYMMDD(event_time) 
ORDER BY (origin_resolution, event_time);

CREATE TABLE shard.completed_viewings (
    id UUID,
    event_time DateTime64(3, 'UTC'),
    user_id UUID,
    video_id UInt32
) ENGINE = ReplicatedMergeTree('/clickhouse/tables/{shard}/completed_viewings', '{replica}') 
PARTITION BY toYYYYMMDD(event_time) 
ORDER BY event_time;

CREATE TABLE shard.filter_applications (
    id UUID,
    event_time DateTime64(3, 'UTC'),
    user_id UUID,
    filter_type Enum8('genre', 'rate', 'actors'),
    filter_value String
) ENGINE = ReplicatedMergeTree('/clickhouse/tables/{shard}/filter_applications', '{replica}') 
PARTITION BY toYYYYMMDD(event_time) 
ORDER BY (filter_type, filter_value, event_time);

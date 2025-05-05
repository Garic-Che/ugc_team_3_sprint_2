CREATE TABLE default.clicks
ENGINE = Distributed('{cluster}', '', clicks, rand())
AS shard.clicks;

CREATE TABLE default.visits
ENGINE = Distributed('{cluster}', '', visits, rand())
AS shard.visits;

CREATE TABLE default.resolution_changes
ENGINE = Distributed('{cluster}', '', resolution_changes, rand())
AS shard.resolution_changes;

CREATE TABLE default.completed_viewings
ENGINE = Distributed('{cluster}', '', completed_viewings, rand())
AS shard.completed_viewings;

CREATE TABLE default.filter_applications
ENGINE = Distributed('{cluster}', '', filter_applications, rand())
AS shard.filter_applications;
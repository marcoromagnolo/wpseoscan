create table if not exists vector_state (
    id int auto_increment,
	creation_time timestamp not null,
	primary key(id)
);

create table if not exists post_top_keywords (
	keyword varchar(255) not null,
    post_id int not null,
	primary key(keyword, post_id)
);

create table if not exists posts (
	post_id int not null,
	names text default null,
    i int not null,
	primary key(post_id)
);

create table if not exists post_links (
    id int auto_increment,
    post_id int not null,
	keyword varchar(255) not null,
    link_post_id int not null,
	primary key(id)
);
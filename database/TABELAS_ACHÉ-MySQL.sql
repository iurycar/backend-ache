create database if not exists `ache_db`;
use `ache_db`;

drop table if exists `sheet`;
drop table if exists `metadata`;
drop table if exists `AUTH`;

create table `AUTH` (
			`user_id`		varchar(40)		not null,
            `email`			varchar(100)	not null unique,
            `password_hash`	varchar(255)	not null,
            `name`			varchar(30)		not null,
            `last_name`		varchar(60)		not null,
            `role`			varchar(20)		not null,
            primary key(`user_id`)
);
describe `AUTH`;

create table `metadata` (
			`id_file`		varchar(50)		not null,
            `original_name`	varchar(100)	not null,
            `import_date`	DATETIME		not null,
            `AUTH_user_id`	varchar(40)		not null,
            primary key(`id_file`)
);

alter table `metadata`
add constraint `meta_auth_fk`
foreign key(`AUTH_user_id`)
references `auth` (`user_id`);

describe `metadata`;

create table `sheet` (
			`num`				varchar(4)		not null,
            `classe`			varchar(25)		not null,
            `category`			varchar(25)		not null,
            `phase`				varchar(25)		not null,
            `status`			varchar(6)		not null,
            `name`				varchar(255)	not null,
            `duration`			varchar(12)		not null,
            `text`				varchar(12)		not null,
            `reference`			varchar(12)		not null,
            `conclusion`		double			not null,
            `METADATA_id_file`	varchar(50)		not null,
            primary key(`num`)
);

alter table `sheet`
add constraint `sheet_meta_fk`
foreign key (`METADATA_id_file`)
references `metadata`	(`id_file`);

describe `sheet`;

insert into `auth` (`user_id`, `email`, `password_hash`, `name`, `last_name`, `role`)
values ('806443c5-9271-464a-a1da-4581c7f766e4', 'usuario@empresa.com.br', '123456', 'Fulano', 'Sicrano Beltrano', 'admin');
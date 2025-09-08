create database if not exists `ache_db`;
use `ache_db`;

create table AUTH (
			`user_id`		varchar(40)		not null,
            `email`			varchar(100)	not null unique,
            `password_hash`	varchar(255)	not null,
            `name`			varchar(30)		not null,
            `last_name`		varchar(60)		not null,
            `role`			varchar(255)	not null,
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
			`id_sheet`			varchar(40)		not null,
            `class`				varchar(25)		not null,
            `category`			varchar(25)		not null,
            `fase`				varchar(25)		not null,
            `condition`			varchar(6)		not null,
            `name`				varchar(50)		not null,
            `duration`			smallint		not null,
            `text`				smallint		not null,
            `reference`			smallint		not null,
            `METADATA_id_file`	varchar(50)		not null,
            primary key(`id_sheet`)
);

alter table `sheet`
add constraint `sheet_meta_fk`
foreign key (`METADATA_id_file`)
references `metadata`	(`id_file`);

describe `sheet`;

insert into `auth` (`user_id`, `email`, `password_hash`, `name`, `last_name`, `role`)
values ('806443c5-9271-464a-a1da-4581c7f766e4', 'usuario@empresa.com.br', '123456', 'Fulano', 'Sicrano Beltrano', 'admin');
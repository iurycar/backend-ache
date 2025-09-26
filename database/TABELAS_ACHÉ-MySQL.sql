create database if not exists `ache_db`;
use `ache_db`;

drop table if exists `SHEET`;
drop table if exists `PROJECT`;
drop table if exists `EMPLOYEE`;
drop table if exists `TEAMS`;

create table `TEAMS` (
			`id_team`		varchar(40)		not null,
            `team_name`		varchar(100),
            primary key(`id_team`)
);
describe `TEAMS`;

create table `EMPLOYEE` (
			`user_id`		varchar(40)		not null,
            `email`			varchar(100)	not null unique,
            `password_hash`	varchar(64)		not null,
            `name`			varchar(30)		not null,
            `last_name`		varchar(60)		not null,
            `role`			varchar(20)		not null,
            `id_team`		varchar(40)		not null,
            primary key(`user_id`)
);

alter table `EMPLOYEE`
add constraint `emp_team_fk`
foreign key(`id_team`)
references `TEAMS` (`id_team`);

describe `EMPLOYEE`;

create table `PROJECT` (
			`id_file`		varchar(50)		not null,
            `original_name`	varchar(100)	not null,
            `import_date`	datetime		not null,
            `project_name`  varchar(20)		not null,
            `id_team`		varchar(40)		not null,
            primary key(`id_file`)
);

alter table `PROJECT`
add constraint `proj_team_fk`
foreign key(`id_team`)
references `TEAMS` (`id_team`);

describe `PROJECT`;

create table `SHEET` (
			`id_task` 			smallint		not null		auto_increment,
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
            `start_date` 		datetime,
            `end_date` 			datetime,
            `id_file`			varchar(50)		not null,
            primary key(`id_task`)
);

alter table `SHEET`
add constraint `sheet_proj_fk`
foreign key (`id_file`)
references `PROJECT` (`id_file`);

insert into `TEAMS` (`id_team`, `team_name`)
values ('b80bf62a-6ff5-498e-9b92-12c9d197122d', 'Liora');

insert into `TEAMS` (`id_team`, `team_name`)
values ('061a1547-dd09-4cc7-99e8-4b03b5be7d4b', 'Administradores');

insert into `EMPLOYEE` (`user_id`, `email`, `password_hash`, `name`, `last_name`, `role`, `id_team`)
values ('806443c5-9271-464a-a1da-4581c7f766e4', 'usuario@empresa.com.br', '$2b$12$kBnnDa.GtQFCa.MC7RTr5OWxaqEs/FgCSJpQk4aLk1k6SmFODYJ36', 'Fulano', 'Sicrano Beltrano', 'admin', 'b80bf62a-6ff5-498e-9b92-12c9d197122d');

insert into `EMPLOYEE` (`user_id`, `email`, `password_hash`, `name`, `last_name`, `role`, `id_team`)
values ('b8460203-63b6-49ff-85e2-9e3be1ea20f9', 'usuario2@empresa.com.br', '$2b$12$kBnnDa.GtQFCa.MC7RTr5OWxaqEs/FgCSJpQk4aLk1k6SmFODYJ36', 'Beltrano', 'Fulano Sicrano da Silva', 'admin', 'b80bf62a-6ff5-498e-9b92-12c9d197122d');

insert into `EMPLOYEE` (`user_id`, `email`, `password_hash`, `name`, `last_name`, `role`, `id_team`)
values ('7bdd3008-26c9-4e83-9317-6e98628819ca', 'usuario3@empresa.com.br', '$2b$12$kBnnDa.GtQFCa.MC7RTr5OWxaqEs/FgCSJpQk4aLk1k6SmFODYJ36', 'Sicrano', 'Beltrano Fulano de Oliveira', 'admin', '061a1547-dd09-4cc7-99e8-4b03b5be7d4b');
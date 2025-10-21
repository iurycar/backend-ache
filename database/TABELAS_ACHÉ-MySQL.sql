create database if not exists `ache_db`;
use `ache_db`;

drop table if exists `SHEET`;
drop table if exists `PROJECT`;
drop table if exists `EMPLOYEE`;
drop table if exists `TEAMS`;
drop table if exists `ADDRESS`;

-- Autenticação e times

create table `TEAMS` (
			`id_team`				varchar(40)		not null,
            `completed_projects` 	smallint,
            `name_team`				varchar(100),
            constraint team_id_pk primary key(`id_team`)
);
describe `TEAMS`;

create table `ADDRESS` (
			`id_address`		smallint		not null,
            `street_address`	varchar(128)	not null,
            `postal_code`		varchar(12)		not null,
            `city`				varchar(32)		not null,
            `state`				varchar(25)		not null,
            `country`			char(3)			not null,
            constraint address_id_pk primary key(`id_address`)
);

create table `EMPLOYEE` (
			`user_id`		varchar(40)		not null,
            `email`			varchar(100)	not null,
            `password_hash`	varchar(64)		not null,
            `first_name`	varchar(30)		not null,
            `last_name`		varchar(60)		not null,
            `role`			varchar(20)		not null,
            `cellphone` 	varchar(20)		not null,
            `active`		boolean			not null,
            `id_team`		varchar(40)		not null,
            `id_address`	smallint		not null,
            constraint emp_id_pk primary key(`user_id`),
            constraint emp_email_un unique (`email`)
);

alter table `EMPLOYEE`
add constraint `emp_team_fk`
foreign key(`id_team`)
references `TEAMS` (`id_team`);

alter table `EMPLOYEE`
add constraint `emp_adress_fk`
foreign key(`id_address`)
references `ADDRESS` (`id_address`);

describe `EMPLOYEE`;

-- Projetos e Planilhas (TAREFAS)

create table `PROJECT` (
			`id_file`		varchar(50)		not null,
            `original_name`	varchar(100)	not null,
            `import_date`	datetime		not null,
            `project_name`  varchar(20)		not null,
            `completed`		boolean			default		0,
            `closing_date`	datetime,
            `id_team`		varchar(40)		not null,
            constraint project_id_pk primary key(`id_file`)
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
            `deadline`			datetime,
            `end_date` 			datetime,
            `id_file`			varchar(50)		not null,
            `user_id`			varchar(40),
            constraint sheet_id_pk primary key(`id_task`)
);

alter table `SHEET`
add constraint `sheet_proj_fk`
foreign key (`id_file`)
references `PROJECT` (`id_file`);

alter table `SHEET`
add constraint `sheet_emp_fk`
foreign key (`user_id`)
references `EMPLOYEE` (`user_id`);

describe `sheet`;

-- Inventário/Estoque

insert into `TEAMS` (`id_team`, `name_team`)
values ('b80bf62a-6ff5-498e-9b92-12c9d197122d', 'Liora');

insert into `TEAMS` (`id_team`, `name_team`)
values ('061a1547-dd09-4cc7-99e8-4b03b5be7d4b', 'Administradores');

insert into `ADDRESS` (`id_address`, `street_address`, `postal_code`, `city`, `state`, `country`)
values (1, 'Av. Lins de Vasconcelos, 1222', '04112-002', 'São Paulo', 'SP', 'BR');

insert into `ADDRESS` (`id_address`, `street_address`, `postal_code`, `city`, `state`, `country`)
values (2, 'Av. Paulista, 1106', '01311-000', 'São Paulo', 'SP', 'BR');

insert into `EMPLOYEE` (`user_id`, `email`, `password_hash`, `first_name`, `last_name`, `role`, `cellphone`, `active`, `id_team`, `id_address`)
values ('806443c5-9271-464a-a1da-4581c7f766e4', 'usuario@empresa.com.br', '$2b$12$kBnnDa.GtQFCa.MC7RTr5OWxaqEs/FgCSJpQk4aLk1k6SmFODYJ36', 'Iury', 'Cardoso Araujo', 'Gerente de Projeto', '+55 77 98176-9384', TRUE, 'b80bf62a-6ff5-498e-9b92-12c9d197122d', 1);

insert into `EMPLOYEE` (`user_id`, `email`, `password_hash`, `first_name`, `last_name`, `role`, `cellphone`, `active`, `id_team`, `id_address`)
values ('983143c5-5471-483g-a2db-7284d3a754pa', 'usuario2@empresa.com.br', '$2b$12$kBnnDa.GtQFCa.MC7RTr5OWxaqEs/FgCSJpQk4aLk1k6SmFODYJ36', 'Fulano', 'Sicrano Beltrano', 'QA', '+55 11 99823-0494', TRUE, 'b80bf62a-6ff5-498e-9b92-12c9d197122d', 2);

insert into `EMPLOYEE` (`user_id`, `email`, `password_hash`, `first_name`, `last_name`, `role`, `cellphone`, `active`, `id_team`, `id_address`)
values ('b8460203-63b6-49ff-85e2-9e3be1ea20f9', 'usuario3@empresa.com.br', '$2b$12$kBnnDa.GtQFCa.MC7RTr5OWxaqEs/FgCSJpQk4aLk1k6SmFODYJ36', 'Beltrano', 'Fulano Sicrano da Silva', 'Desenvolver Python', '+55 75 91234-5678', FALSE, 'b80bf62a-6ff5-498e-9b92-12c9d197122d', 1);

insert into `EMPLOYEE` (`user_id`, `email`, `password_hash`, `first_name`, `last_name`, `role`, `cellphone`, `active`, `id_team`, `id_address`)
values ('7bdd3008-26c9-4e83-9317-6e98628819ca', 'usuario4@empresa.com.br', '$2b$12$kBnnDa.GtQFCa.MC7RTr5OWxaqEs/FgCSJpQk4aLk1k6SmFODYJ36', 'Sicrano', 'Beltrano Fulano de Oliveira', 'admin', '+55 11 99032-4125', TRUE, '061a1547-dd09-4cc7-99e8-4b03b5be7d4b', 2);
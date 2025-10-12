use `ache_db`;
describe `sheet`;
describe `project`;
describe `employee`;
describe `teams`;

delete from `employee` where user_id = 'b8460203-63b6-49ff-85e2-9e3be1ea20f9';
delete from `teams` where id_team = '806443c5-9271-464a-a1da-4581c7f766e4';
delete from `sheet` where id_file = 'c17545cd-5cf4-4573-82f1-a163ff5d3a50.xlsx';
delete from `project` where id_file = 'c17545cd-5cf4-4573-82f1-a163ff5d3a50.xlsx';


alter table `sheet`
modify column `responsible` varchar(120);


update `employee`
set `password_hash` = '$2b$12$kBnnDa.GtQFCa.MC7RTr5OWxaqEs/FgCSJpQk4aLk1k6SmFODYJ36'
where `user_id` = '806443c5-9271-464a-a1da-4581c7f766e4';

select * from `address`;
select * from `task_history`;
select * from `project`;
select * from `sheet`;
select * from `employee`;
select * from `teams`;

select * from `sheet` where `id_file` = 'bb2dc2cb-2ff4-460a-8a81-bca8e0ceeb23.xlsx';

UPDATE `sheet` SET `start_date` = NOW() WHERE (`start_date` IS NULL) AND (`conclusion` > 0 AND `conclusion` < 1);

select `completed`, `id_file`, `project_name` from `project` where `id_team` = 'b80bf62a-6ff5-498e-9b92-12c9d197122d';
select COUNT(*) from sheet where `id_file` = 'c17545cd-5cf4-4573-82f1-a163ff5d3a50.xlsx';

SELECT COUNT(*) AS 'concluidas' FROM `sheet` WHERE `id_file` = 'c17545cd-5cf4-4573-82f1-a163ff5d3a50.xlsx' AND `conclusion` = 1;
SELECT COUNT(*) AS 'overdue' FROM `sheet` WHERE `id_file` = 'c17545cd-5cf4-4573-82f1-a163ff5d3a50.xlsx' AND `conclusion` < 1 AND start_date < NOW();
SELECT `start_date`, `duration`, `conclusion` FROM `sheet` WHERE `id_file` = 'c17545cd-5cf4-4573-82f1-a163ff5d3a50.xlsx' AND `start_date` IS NOT NULL AND `conclusion` < 1;

select start_date from `sheet`;

update `sheet` set `start_date` = '2025-08-24 12:03:00' where `id_task` = 3283;

select max(`num`) from `sheet`;

insert into `EMPLOYEE` (`user_id`, `email`, `password_hash`, `name`, `last_name`, `role`, `id_team`)
values ('b8460203-63b6-49ff-85e2-9e3be1ea20f9', 'usuario2@empresa.com.br', '$2b$12$kBnnDa.GtQFCa.MC7RTr5OWxaqEs/FgCSJpQk4aLk1k6SmFODYJ36', 'Beltrano', 'Fulano Sicrano da Silva', 'admin', 'b80bf62a-6ff5-498e-9b92-12c9d197122d');

start transaction;

update `sheet` set classe = 'Nada Nada' where num = '131';

commit;

UPDATE sheet SET start_date = CASE WHEN (start_date IS NULL OR start_date = '') AND (CASE WHEN COALESCE(conclusion,0) > 1 THEN COALESCE(conclusion,0)/100 ELSE COALESCE(conclusion,0) END ) > 0 THEN NOW() ELSE start_date END, end_date = CASE WHEN (end_date IS NULL OR end_date = '') AND ( CASE WHEN COALESCE(conclusion,0) > 1 THEN COALESCE(conclusion,0)/100 ELSE COALESCE(conclusion,0) END ) >= 1 THEN NOW() ELSE end_date END  WHERE id_file = :id_file
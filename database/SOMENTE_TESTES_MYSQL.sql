use `ache_db`;
describe `sheets`;
describe `projects`;
describe `employees`;
describe `teams`;
describe `address`;

delete from `employee` where user_id = 'b8460203-63b6-49ff-85e2-9e3be1ea20f9';
delete from `teams` where id_team = '806443c5-9271-464a-a1da-4581c7f766e4';
delete from `sheet` where id_file = '536b387f-9800-493c-8e32-4f7dfad4063e.xlsx';
delete from `project` where id_file = '536b387f-9800-493c-8e32-4f7dfad4063e.xlsx';

alter table `sheet`
drop column `overdue`;

alter table `sheet`
add column `overdue` smallint;

ALTER TABLE `PROJECT` 
CHANGE COLUMN `end_date` `closing_date` DATETIME;

update `employee`
set `password_hash` = '$2b$12$kBnnDa.GtQFCa.MC7RTr5OWxaqEs/FgCSJpQk4aLk1k6SmFODYJ36'
where `user_id` = '806443c5-9271-464a-a1da-4581c7f766e4';

select * from `address`;
select * from `projects`;
select * from `sheets`;
select * from `employees`;
select * from `teams`;

SELECT COALESCE(MAX(`num`), 1) FROM `SHEETS` WHERE `id_file` = 'aaa';

select `num`, `start_date`, `deadline`, `status` from `sheet` where `user_id` = '806443c5-9271-464a-a1da-4581c7f766e4' and `conclusion` < 1;



SELECT COUNT(*) AS 'concluidas' FROM `sheet` WHERE `id_file` = 'c17545cd-5cf4-4573-82f1-a163ff5d3a50.xlsx' AND `conclusion` = 1;
SELECT COUNT(*) AS 'overdue' FROM `sheet` WHERE `id_file` = 'c17545cd-5cf4-4573-82f1-a163ff5d3a50.xlsx' AND `conclusion` < 1 AND start_date < NOW();

select date_add(`start_date`, INTERVAL 16 DAY) as `nova_date` from `sheet` where `start_date` is not null;

select count(*) as `overdue` from `sheet` where `start_date` is not null and `deadline` is not null and datediff(NOW(), `deadline`) > 0;

UPDATE `sheet` SET `duration` = REPLACE(`duration`,' dias',''); 

UPDATE `sheet` SET `deadline` = DATE_ADD(`start_date`, INTERVAL `duration` DAY) WHERE `start_date` IS NOT NULL AND `end_date` IS NULL AND `deadline` IS NULL;

SELECT COUNT(*) FROM `SHEET` JOIN `PROJECT` ON `SHEET`.`id_file` = `PROJECT`.`id_file` WHERE `id_team` = 'b80bf62a-6ff5-498e-9b92-12c9d197122d' AND `deadline` IS NOT NULL AND `start_date` IS NOT NULL AND datediff(NOW(), `deadline`) > 0;

update `sheet` set `deadline` = '2025-08-28 21:45:31' where `id_task` = 4027;

select max(`num`) from `sheet`;

insert into `EMPLOYEE` (`user_id`, `email`, `password_hash`, `name`, `last_name`, `role`, `id_team`)
values ('b8460203-63b6-49ff-85e2-9e3be1ea20f9', 'usuario2@empresa.com.br', '$2b$12$kBnnDa.GtQFCa.MC7RTr5OWxaqEs/FgCSJpQk4aLk1k6SmFODYJ36', 'Beltrano', 'Fulano Sicrano da Silva', 'admin', 'b80bf62a-6ff5-498e-9b92-12c9d197122d');
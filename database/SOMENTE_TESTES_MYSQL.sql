use `ache_db`;
describe `sheet`;
describe `project`;
describe `employee`;
describe `teams`;

delete from `employee` where user_id = 'b8460203-63b6-49ff-85e2-9e3be1ea20f9';
delete from `teams` where id_team = '806443c5-9271-464a-a1da-4581c7f766e4';
delete from `sheet` where id_file = '536b387f-9800-493c-8e32-4f7dfad4063e.xlsx';
delete from `project` where id_file = '536b387f-9800-493c-8e32-4f7dfad4063e.xlsx';

alter table `sheet`
modify column `responsible` varchar(120);

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
select * from `project`;
select * from `sheet`;
select * from `employee`;
select * from `teams`;

select `city`, `state`, `country` from `address` where `id_address` = 1; 

update `sheet` set `user_id` = null where `id_task` = 17;

select max(num) from `sheet` where `id_file` = '536b387f-9800-493c-8e32-4f7dfad4063e.xlsx';

select * from `sheet` where `id_file` = 'a5108b4f-e14c-4761-ac46-c2f2d43acc66.xlsx';

select COUNT(*) from `sheet` where `id_file` = 'c17545cd-5cf4-4573-82f1-a163ff5d3a50.xlsx';

SELECT COUNT(*) AS 'concluidas' FROM `sheet` WHERE `id_file` = 'c17545cd-5cf4-4573-82f1-a163ff5d3a50.xlsx' AND `conclusion` = 1;
SELECT COUNT(*) AS 'overdue' FROM `sheet` WHERE `id_file` = 'c17545cd-5cf4-4573-82f1-a163ff5d3a50.xlsx' AND `conclusion` < 1 AND start_date < NOW();
SELECT `start_date`, `duration`, `conclusion` FROM `sheet` WHERE `id_file` = 'c17545cd-5cf4-4573-82f1-a163ff5d3a50.xlsx' AND `start_date` IS NOT NULL AND `conclusion` < 1;

select date_add(`start_date`, INTERVAL 16 DAY) as `nova_date` from `sheet` where `start_date` is not null;

select count(*) as `overdue` from `sheet` where `start_date` is not null and `deadline` is not null and datediff(NOW(), `deadline`) > 0;

UPDATE `sheet` SET `duration` = REPLACE(`duration`,' dias',''); 

UPDATE `sheet` SET `deadline` = DATE_ADD(`start_date`, INTERVAL `duration` DAY) WHERE `start_date` IS NOT NULL AND `end_date` IS NULL AND `deadline` IS NULL;

SELECT COUNT(*) FROM `SHEET` JOIN `PROJECT` ON `SHEET`.`id_file` = `PROJECT`.`id_file` WHERE `id_team` = 'b80bf62a-6ff5-498e-9b92-12c9d197122d' AND `deadline` IS NOT NULL AND `start_date` IS NOT NULL AND datediff(NOW(), `deadline`) > 0;

select * from `sheet` where `user_id` is not null;

update `sheet` set `deadline` = '2025-08-28 21:45:31' where `id_task` = 4027;

select max(`num`) from `sheet`;

insert into `EMPLOYEE` (`user_id`, `email`, `password_hash`, `name`, `last_name`, `role`, `id_team`)
values ('b8460203-63b6-49ff-85e2-9e3be1ea20f9', 'usuario2@empresa.com.br', '$2b$12$kBnnDa.GtQFCa.MC7RTr5OWxaqEs/FgCSJpQk4aLk1k6SmFODYJ36', 'Beltrano', 'Fulano Sicrano da Silva', 'admin', 'b80bf62a-6ff5-498e-9b92-12c9d197122d');
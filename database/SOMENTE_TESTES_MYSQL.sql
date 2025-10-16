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

alter table `project`
add column `end_date` datetime;

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

update `sheet` set `user_id` = null where `id_task` = 17;

select max(num) from `sheet` where `id_file` = '536b387f-9800-493c-8e32-4f7dfad4063e.xlsx';

select * from `sheet` where `id_file` = 'a5108b4f-e14c-4761-ac46-c2f2d43acc66.xlsx';

select count(*) from `sheet` where ``

update `sheet` set `conclusion` = 1 where `id_file` = 'a5108b4f-e14c-4761-ac46-c2f2d43acc66.xlsx';

UPDATE `sheet` SET `end_date` = NOW() WHERE (`end_date` IS NULL) AND (`conclusion` >= 1);

update `project` set `completed` = false where `id_file` = '7e164ca8-cf6d-4a0b-885a-d7a41916f819.xlsx';

select `completed`, `id_file`, `project_name` from `project` where `id_team` = 'b80bf62a-6ff5-498e-9b92-12c9d197122d';
select COUNT(*) from `sheet` where `id_file` = 'c17545cd-5cf4-4573-82f1-a163ff5d3a50.xlsx';

SELECT COUNT(*) AS 'concluidas' FROM `sheet` WHERE `id_file` = 'c17545cd-5cf4-4573-82f1-a163ff5d3a50.xlsx' AND `conclusion` = 1;
SELECT COUNT(*) AS 'overdue' FROM `sheet` WHERE `id_file` = 'c17545cd-5cf4-4573-82f1-a163ff5d3a50.xlsx' AND `conclusion` < 1 AND start_date < NOW();
SELECT `start_date`, `duration`, `conclusion` FROM `sheet` WHERE `id_file` = 'c17545cd-5cf4-4573-82f1-a163ff5d3a50.xlsx' AND `start_date` IS NOT NULL AND `conclusion` < 1;

select `start_date` from `sheet`;

update `sheet` set `start_date` = '2025-10-12 00:12:06' where `id_task` = 3734;

select max(`num`) from `sheet`;

insert into `EMPLOYEE` (`user_id`, `email`, `password_hash`, `name`, `last_name`, `role`, `id_team`)
values ('b8460203-63b6-49ff-85e2-9e3be1ea20f9', 'usuario2@empresa.com.br', '$2b$12$kBnnDa.GtQFCa.MC7RTr5OWxaqEs/FgCSJpQk4aLk1k6SmFODYJ36', 'Beltrano', 'Fulano Sicrano da Silva', 'admin', 'b80bf62a-6ff5-498e-9b92-12c9d197122d');
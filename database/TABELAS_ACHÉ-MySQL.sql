use `ache_db`;
describe `sheet`;
describe `project`;
describe `employee`;
describe `teams`;

delete from `employee` where user_id = 'b8460203-63b6-49ff-85e2-9e3be1ea20f9';
delete from `teams` where id_team = '806443c5-9271-464a-a1da-4581c7f766e4';
delete from `sheet` where id_file = 'b8460203-63b6-49ff-85e2-9e3be1ea20f9.xlsx';
delete from `project` where id_file = 'b8460203-63b6-49ff-85e2-9e3be1ea20f9.xlsx';

update `employee`
set `password_hash` = '$2b$12$kBnnDa.GtQFCa.MC7RTr5OWxaqEs/FgCSJpQk4aLk1k6SmFODYJ36'
where `user_id` = '806443c5-9271-464a-a1da-4581c7f766e4';

select * from `project`;
select * from `sheet`;
select * from `employee`;
select * from `teams`;

REPAIR TABLE `SHEET`;

select max(`num`) from `sheet`;

insert into `EMPLOYEE` (`user_id`, `email`, `password_hash`, `name`, `last_name`, `role`, `id_team`)
values ('b8460203-63b6-49ff-85e2-9e3be1ea20f9', 'usuario2@empresa.com.br', '$2b$12$kBnnDa.GtQFCa.MC7RTr5OWxaqEs/FgCSJpQk4aLk1k6SmFODYJ36', 'Beltrano', 'Fulano Sicrano da Silva', 'admin', 'b80bf62a-6ff5-498e-9b92-12c9d197122d');
start transaction;

update `sheet` set classe = 'Nada Nada' where num = '131';

commit;

UPDATE sheet SET start_date = CASE WHEN (start_date IS NULL OR start_date = '') AND (CASE WHEN COALESCE(conclusion,0) > 1 THEN COALESCE(conclusion,0)/100 ELSE COALESCE(conclusion,0) END ) > 0 THEN NOW() ELSE start_date END, end_date = CASE WHEN (end_date IS NULL OR end_date = '') AND ( CASE WHEN COALESCE(conclusion,0) > 1 THEN COALESCE(conclusion,0)/100 ELSE COALESCE(conclusion,0) END ) >= 1 THEN NOW() ELSE end_date END  WHERE id_file = :id_file
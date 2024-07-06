SELECT pg_get_serial_sequence('job', 'id');
TRUNCATE TABLE job CASCADE;
ALTER SEQUENCE public.job_id_seq RESTART WITH 1;


SELECT pg_get_serial_sequence('employee', 'id');
TRUNCATE TABLE employee CASCADE;
ALTER SEQUENCE public.employee_id_seq RESTART WITH 1;

SELECT pg_get_serial_sequence('department', 'id');
TRUNCATE TABLE department CASCADE;
ALTER SEQUENCE public.department_id_seq RESTART WITH 1;


drop table job CASCADE;
drop table employee CASCADE;
drop table department CASCADE;
drop table alembic_version CASCADE;


! hacer segundo punto
!puedo desplegar esta imagen en 


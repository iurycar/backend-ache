DROP TABLE sheet PURGE;
DROP TABLE metadata PURGE;
DROP TABLE auth PURGE;

CREATE TABLE auth (
            user_id        VARCHAR2(40)    NOT NULL CONSTRAINT auth_id_pk       PRIMARY KEY,
            email          VARCHAR2(100)   NOT NULL CONSTRAINT auth_email_un    UNIQUE,
            password_hash  VARCHAR2(255)   NOT NULL,
            name           VARCHAR2(20)    NOT NULL,
            last_name      VARCHAR2(55)    NOT NULL,
            role           VARCHAR2(20)    NOT NULL
);
DESC auth;

CREATE TABLE metadata (
            id_file         VARCHAR2(50)                NOT NULL    CONSTRAINT meta_id_pk PRIMARY KEY,
            original_name   VARCHAR2(100)               NOT NULL,
            import_date     VARCHAR2(26)                NOT NULL,
            AUTH_user_id    VARCHAR2(40)                NOT NULL
);

ALTER TABLE metadata
ADD CONSTRAINT meta_auth_fk
FOREIGN KEY (AUTH_user_id)
REFERENCES auth (user_id);

DESC metadata;

CREATE TABLE sheet (
            id_sheet            VARCHAR2(40)    NOT NULL    CONSTRAINT sheet_id_pk PRIMARY KEY,
            class               VARCHAR2(25)    NOT NULL,
            category            VARCHAR2(25)    NOT NULL,
            fase                VARCHAR2(25)    NOT NULL,
            condition           VARCHAR2(6)     NOT NULL,
            name                VARCHAR2(50)    NOT NULL,
            duration            NUMBER(2)       NOT NULL,
            text                NUMBER(4)       NOT NULL,
            reference           NUMBER(3)       NOT NULL,
            METADATA_id_file    VARCHAR2(36)    NOT NULL
);

ALTER TABLE SHEET
ADD CONSTRAINT sheet_meta_fk
FOREIGN KEY (METADATA_id_file)
REFERENCES metadata (id_file);

DESC sheet;

INSERT INTO auth (user_id, email, password_hash, name, last_name, role) 
VALUES ('806443c5-9271-464a-a1da-4581c7f766e4', 'usuario@empresa.com.br', '123456', 'Fulano', 'Sicrano Beltrano', 'admin');
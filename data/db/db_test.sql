/*Init the database. Use the - 5 times to separate statements*/
DROP TABLE IF EXISTS test_table;
-----
CREATE TABLE IF NOT EXISTS test_table
(
  id int NOT NULL,
  name varchar(25) NOT NULL,
  surname varchar(20) NOT NULL,
  PRIMARY KEY (id)
);
-----
INSERT INTO test_table (id, name, surname) VALUES (
  1,
  'Test1',
  't1'
);
-----
INSERT INTO test_table (id, name, surname) VALUES (
  2,
  'Test2',
  't2'
);
-----
INSERT INTO test_table (id, name, surname) VALUES (
  3,
  'Test3',
  't3'
);
-----
INSERT INTO test_table (id, name, surname) VALUES (
  4,
  'Test4',
  't4'
);
-----
INSERT INTO test_table (id, name, surname) VALUES (
  5,
  'Test5',
  't5'
);
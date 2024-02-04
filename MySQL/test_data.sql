INSERT INTO authors (first_name, surname, about, clean_name) VALUES
("Author", "1", "This author does not have an about", "author 1"),
("Author", "2", "This author does not have an about", "author 2"),
("Author", "3", "This author does not have an about", "author 3");

INSERT INTO genres (name, about, clean_name) VALUES
("Genre 1", "This genre does not have an about", "genre 1"),
("Genre 2", "This genre does not have an about", "genre 2"),
("Genre 3", "This genre does not have an about", "genre 3"),
("Genre 4", "This genre does not have an about", "genre 4"),
("Genre 5", "This genre does not have an about", "genre 5"),
("Genre 6", "This genre does not have an about", "genre 6"),
("Genre 7", "This genre does not have an about", "genre 7"),
("Genre 8", "This genre does not have an about", "genre 8"),
("Genre 9", "This genre does not have an about", "genre 9"),
("Genre 10", "This genre does not have an about", "genre 10");

INSERT INTO users (first_name, surname, username, password_hash) VALUES
("user", "1", "user1", "5d557544916fde5c6b162cfcbce84181fb2cbe8798439b643edf96ee4c5826b4"),
("user", "2", "user2", "5d557544916fde5c6b162cfcbce84181fb2cbe8798439b643edf96ee4c5826b4"),
("user", "3", "user3", "5d557544916fde5c6b162cfcbce84181fb2cbe8798439b643edf96ee4c5826b4"),
("user", "4", "user4", "5d557544916fde5c6b162cfcbce84181fb2cbe8798439b643edf96ee4c5826b4");

INSERT INTO books (author_id, title, clean_title, synopsis, cover_image, purchase_link, fiction, release_date, isbn) VALUES 
(1, "Book 1", "book 1", "This book does not have a synopsis", "", "", 1, "2022-2-2", "0111111111"),
(2, "Book 2", "book 2", "This book does not have a synopsis", "", "", 1, "2022-2-2", "0222222222"),
(3, "Book 3", "book 3", "This book does not have a synopsis", "", "", 1, "2022-2-2", "0333333333"),
(2, "Book 4", "book 4", "This book does not have a synopsis", "", "", 1, "2022-2-2", "0444444444"),
(1, "Book 5", "book 5", "This book does not have a synopsis", "", "", 1, "2022-2-2", "0555555555");

INSERT into reviews (book_id, user_id, overall_rating, plot_rating, character_rating) VALUES
(1, 1, 5, 5, 5),
(1, 3, 2, 3, 1),
(2, 1, 3, 2, 3),
(2, 2, 5, 2, 5),
(2, 4, 4, 3, 4),
(3, 2, 5, 3, 4),
(3, 3, 1, 1, 2),
(3, 4, 3, 2, 4),
(4, 1, 3, 2, 5),
(4, 2, 3, 3, 4),
(4, 3, 1, 2, 3),
(4, 4, 4, 3, 5),
(5, 1, 1, 2, 1);

INSERT INTO book_genres (book_id, genre_id, match_strength) VALUES
(1,1,0.697712),
(1,3,0.309666),
(1,5,0.353391),
(1,6,0.169214),
(1,7,0.100102),
(1,8,0.123306),
(1,9,0.950674),
(5,3,0.159634),
(5,5,0.0621221),
(5,6,0.363134),
(5,7,0.28817),
(5,8,0.132367),
(5,9,0.0986237),
(5,10,0.406406),
(2,3,0.498447),
(2,4,1.20635),
(2,6,1.14142),
(2,7,0.84424),
(2,9,0.055903),
(2,10,0.0477423),
(4,3,0.892599),
(4,5,1.05652),
(4,7,1.35095),
(4,10,0.830146),
(3,1,0.137739),
(3,2,0.225134),
(3,3,0.755736),
(3,4,1.1154),
(3,5,0.330547),
(3,7,0.807497);

INSERT INTO sessions (client_id, user_id) VALUES
("asdhjaksnce1263872613", 1),
("adqweqiueqw0812309812", 1),
("zxmcabvzxcn1231231235", 1),
("poipoqwerwrw983453453", 3),
("swcdecwftrbr132788943", 3);

INSERT INTO sessions (client_id, user_id, date_added) VALUES
("swcdeawftrbr132788943", 2, "2021-2-2"),
("sdfasdvnjtit987652678", 1, "2020-3-4"),
("lmoijbnernub125392872", 4, "2022-12-8");

INSERT INTO reading_list_names (list_name, user_id) VALUES
("Want to Read", 1),
("Currently Reading", 1),
("Have Read", 1),
("Want to Read", 2),
("Currently Reading", 2),
("Have Read", 2),
("Want to Read", 3),
("Currently Reading", 3),
("Have Read", 3),
("Want to Read", 4),
("Currently Reading", 4),
("Have Read", 4);
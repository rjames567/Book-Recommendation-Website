INSERT INTO authors (first_name, surname, about, clean_name) VALUES
('Kristin', 'Hannah', 'This author does not have an about', 'kristin hannah'),
('B.A.', 'Paris', 'This author does not have an about', 'ba paris'),
('George', 'Orwell', ' This author does not have an about', 'george orwell'),
('Mary', 'E. Pearson', 'This author does not have an about', 'mary e pearson'),
('Kurt', 'Vonnegut Jr.', 'This author does not have an about', 'kurt vonnegut jr'),
('Rick', 'Riordan', 'This author does not have an about', 'rick riordan'),
('Madeleine', "L'Engle", 'This author does not have an about', 'madeleine lengle'),
('Alyson', 'Noel', 'This author does not have an about', 'alyson noel'),
('Jay', 'Asher', 'This author does not have an about', 'jay asher'),
('Marie', 'Kondo', 'This author does not have an about', 'marie kondo'),
('William', 'Goldman', 'This author does not have an about', 'william goldman'),
('Barbara', 'Kingsolver', 'This author does not have an about', 'barbara kingsolver'),
('Susan', 'Ee', 'This author does not have an about', 'susan ee'),
('Gregory', 'Maguire', 'This author does not have an about', 'gregory maguire'),
('Bill', 'Bryson', 'This author does not have an about', 'bill bryson'),
('Jennifer', 'L. Armentrout', 'This author does not have an about', 'jennifer l armentrout'),
('Kristin', 'Cashore', 'This author does not have an about', 'kristin cashore'),
('Aziz', 'Ansari', 'This author does not have an about', 'aziz ansari'),
('Abbi', 'Glines', 'This author does not have an about', 'abbi glines');

INSERT INTO books (author_id, title, clean_title, synopsis, cover_image, purchase_link, fiction, release_date, isbn) VALUES
(4, "The Nightingale", "the nightingale", "", "", "", 1, "2015-01-01", "41125521"),
(3, "Animal Farm", "animal farm", "", "", "", 1, "2003-01-01", "2207778"),
(7, "The Kiss of Deception (The Remnant Chronicles, #1)", "the kiss of deception the remnant chronicles 1", "", "", "", 1, "2014-01-01", "22617247"),
(9, "The Sea of Monsters (Percy Jackson and the Olympians, #2)", "the sea of monsters percy jackson and the olympians 2", "", "", "", 1, "2006-01-01", "43554"),
(9, "The Son of Neptune (The Heroes of Olympus, #2)", "the son of neptune the heroes of olympus 2", "", "", "", 1, "2011-01-01", "14406312"),
(9, "The Last Olympian (Percy Jackson and the Olympians, #5)", "the last olympian percy jackson and the olympians 5", "", "", "", 1, "2009-01-01", "4551489"),
(9, "The Sword of Summer (Magnus Chase and the Gods of Asgard, #1)", "the sword of summer magnus chase and the gods of asgard 1", "", "", "", 1, "2015-01-01", "21400019"),
(9, "The Red Pyramid (Kane Chronicles, #1)", "the red pyramid kane chronicles 1", "", "", "", 1, "2010-01-01", "346572"),
(11, "Evermore (The Immortals, #1)", "evermore the immortals 1", "", "", "", 1, "1990-01-01", "4021549"),
(13, "The Life-Changing Magic of Tidying Up: The Japanese Art of Decluttering and Organizing", "the lifechanging magic of tidying up the japanese art of decluttering and organizing", "", "", "", 1, "2014-01-01", "41711738"),
(15, "The Poisonwood Bible", "he poisonwood bible", "", "", "", 1, "2005-01-01", "810663"),
(16, "Angelfall (Penryn & the End of Days, #1)", "angelfall penryn  the end of days 1", "", "", "", 1, "2013-01-01", "16435765"),
(18, "A Walk in the Woods", "a walk in the woods", "", "", "", 1, "1990-01-01", "613469"),
(19, "Onyx (Lux, #2)", "onyx lux 2", "", "", "", 1, "2012-01-01", "18211575"),
(19, "Opal (Lux, #3)", "opal lux 3", "", "", "", 1, "2012-01-01", "18591132"),
(19, "Origin (Lux, #4)", "origin lux 4", "", "", "", 1, "2013-01-01", "19259997"),
(20, "Graceling (Graceling Realm, #1)", "graceling graceling realm 1", "", "", "", 1, "2008-01-01", "3270810"),
(21, "Modern Romance", "modern romance", "", "", "", 1, "2015-01-01", "43014915");

INSERT INTO reading_lists (user_id, list_id, book_id) VALUES -- users 1,2,3,4
(1, 1, 6),
(1, 1, 9),
(1, 2, 13),
(2, 4, 13),
(2, 4, 7),
(2, 4, 15),
(2, 5, 16),
(2, 5, 1),
(3, 7, 7),
(3, 7, 8),
(3, 8, 2),
(3, 8, 20),
(4, 10, 11),
(4, 10, 13),
(4, 10, 15),
(4, 10, 1),
(4, 11, 5);

INSERT INTO reading_list_names (list_name, user_id) VALUES
("Test list", 1),
("Test list", 2);

INSERT INTO reading_lists (user_id, list_id, book_id) VALUES
(1, 13, 21)
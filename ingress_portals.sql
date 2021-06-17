CREATE TABLE IF NOT EXISTS `ingress_portals` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `external_id` varchar(35) COLLATE utf8mb4_bin DEFAULT NULL,
  `lat` double(18,14) DEFAULT NULL,
  `lon` double(18,14) DEFAULT NULL,
  `name` varchar(128) COLLATE utf8mb4_bin DEFAULT NULL,
  `url` varchar(200) COLLATE utf8mb4_bin DEFAULT NULL,
  `updated` bigint(11) NOT NULL,
  `imported` bigint(11) DEFAULT NULL,
  `checked` tinyint(4) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `external_id` (`external_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
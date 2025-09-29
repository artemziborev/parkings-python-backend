// Инициализация MongoDB для parking_db
db = db.getSiblingDB('parking_db');

// Создаем коллекцию parkings
db.createCollection('parkings');

// Создаем геопространственный индекс для поиска по координатам
db.parkings.createIndex({"center": "2dsphere"});

// Создаем текстовый индекс для поиска по названию
db.parkings.createIndex({"name.ru": "text", "name.en": "text"});

// Создаем индекс для поиска по литере/номеру
db.parkings.createIndex({"litera": 1});

print("MongoDB initialization completed for parking_db");

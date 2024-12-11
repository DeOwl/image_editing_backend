# Применение фильтров к изображению
Проект создан в рамках курса "Разработка интернет-приложений" (МГТУ им. Н.Э. Баумана, ИУ5, 5 семестр). Включает в себя фронтенд, бэкенд и РПЗ.

Веб-приложение выполнено в формате "Услуги/заявки", где услуги - фильтры, а заявки — очереди применения фильтров к изображению. Подробнее о проекте можно узнать в РПЗ.

## Ссылки на репозитории проекта:
1. [Фронтенд](https://github.com/DeOwl/image_editing_frontend)
2. [Бэкенд](https://github.com/DeOwl/image_editing_backend)

## Бэкенд

### Ветки
- **ssr**: создание базового интерфейса, состоящего из трёх страниц. Первая для просмотра списка услуг в виде карточек с наименованием и картинкой. При клике по карточке происходит переход на вторую страницу с подробной информацией об услуге. Фильтрация услуг.
- **db**: разработка структуры базы данных и ее подключение к бэкенду.
- **web_service**: создание веб-сервиса для получения/редактирования данных из БД, разработка всех методов для реализации итоговой бизнес-логики приложения. Соответствующая ветка фронтенда - base-spa.
- **swagger**: завершение бэкенда для SPA, добавление авторизации через JWT, Swagger.

### Стек технологий
- Python
- Django
- DRF
- Docker
- Minio
- Redis
- Postgres
- Swagger

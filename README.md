# DevOps Pet Project

Учебный проект: веб-приложение на FastAPI и PostgreSQL с развёртыванием на Linux-ВМ в Yandex Cloud через GitLab CI/CD, мониторингом и зашифрованными резервными копиями в Google Drive.

Приложение позволяет создавать и просматривать посты через API и простой интерфейс на HTML, CSS и JavaScript. Основной фокус проекта — практика эксплуатации сервиса: сборка образов, деплой, диагностика, оповещения и восстановление данных.

## Что реализовано

- Контейнеризация приложения и PostgreSQL через Docker Compose, проверки здоровья и постоянные тома для данных.
- GitLab CI/CD: Ruff, pytest с отдельной PostgreSQL, сборка и публикация образа с тегом Git SHA, деплой по SSH.
- Проверка SSH-ключа сервера через `known_hosts`; повторные попытки скачивания образов при сетевых ошибках.
- Prometheus: метрики FastAPI и Node Exporter на сервере.
- Grafana: дашборд запросов и доступности API, правила оповещений из YAML, отправка уведомлений через Gmail SMTP.
- Резервные копии PostgreSQL: `pg_dump`, проверка оглавления архива, шифрование rclone crypt и загрузка в Google Drive.
- Ежедневный systemd timer, хранение копий 7 дней на сервере и 30 дней в облаке.
- Метрика времени последнего успешного бэкапа и алерт при возрасте более 26 часов.
- Страницы описания приложения резервного копирования и политики конфиденциальности через GitLab Pages.

Это учебная конфигурация. Nginx, HTTPS приложения, автоматический откат, Ansible и Terraform пока находятся в плане.

## Архитектура сервера

```mermaid
flowchart LR
    Browser[Браузер] -->|HTTP :8000| App[FastAPI + JS-интерфейс]
    App --> DB[(PostgreSQL)]
    Prom[Prometheus] -->|/metrics| App
    Prom --> Node[Node Exporter]
    Grafana[Grafana] --> Prom
    Grafana -->|SMTP| Mail[Почта]
    Timer[systemd timer] --> Backup[Скрипт резервного копирования]
    Backup -->|pg_dump| DB
    Backup -->|rclone crypt| Drive[Google Drive]
    Backup --> Metric[Файл метрики .prom]
    Node --> Metric
    CI[GitLab CI/CD] -->|SSH + Compose| App
```

Стрелки от Prometheus обозначают опрос источников метрик. Grafana и Prometheus привязаны к `127.0.0.1` ВМ и доступны администратору через SSH-туннель. PostgreSQL на сервере не публикует порт наружу, Node Exporter доступен по сети Compose.

## Стек

| Область | Инструменты |
|---|---|
| Приложение | Python 3.13, FastAPI, Uvicorn, SQLAlchemy, PostgreSQL 16 |
| Интерфейс | HTML, CSS, JavaScript, Fetch API |
| Контейнеры | Docker, Docker Compose, GitLab Container Registry |
| CI/CD | GitLab CI/CD; дополнительный workflow GitHub Actions |
| Проверки | Ruff, pytest, FastAPI TestClient |
| Мониторинг | Prometheus, Grafana, Node Exporter |
| Бэкапы | pg_dump / pg_restore, rclone crypt, Google Drive, systemd |
| Инфраструктура | Linux-ВМ в Yandex Cloud, SSH |

## Структура репозитория

```text
.
├── apps/                          # FastAPI, модели и подключение к БД
├── frontend/                      # Интерфейс создания и просмотра постов
├── tests/                         # Проверки API с отдельной тестовой БД
├── init/                          # SQL для первичной инициализации PostgreSQL
├── monitoring/
│   ├── prometheus.yml             # Источники метрик
│   └── grafana/alerting/           # Правила API и свежести бэкапов
├── scripts/backup-postgres.sh      # Создание, загрузка и очистка копий
├── systemd/                       # Сервис и таймер резервного копирования
├── docs/oauth/                    # Публичные страницы OAuth-приложения
├── Dockerfile
├── docker-compose.yml             # Локальный запуск
├── compose.deploy.yml             # Серверный запуск готового образа
├── .gitlab-ci.yml
└── .github/workflows/ci.yml
```

## Локальный запуск

Нужны Git, Docker и Docker Compose v2.

```bash
git clone https://gitlab.com/goha46/devops-pet-project.git
cd devops-pet-project
docker compose up -d --build
docker compose ps
```

| Сервис | Адрес |
|---|---|
| Веб-интерфейс | http://localhost:8000/ui/ |
| Swagger UI | http://localhost:8000/docs |
| Health endpoint | http://localhost:8000/health |
| Метрики приложения | http://localhost:8000/metrics |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |
| PostgreSQL для локальных инструментов | `localhost:5433` |

Локальный Compose использует учебные реквизиты PostgreSQL: база `app_db`, пользователь `app_user`, пароль `app_pass`. Данные сохраняются в томе `pgdata`.

Node Exporter определён только в серверном Compose. Общий `prometheus.yml` также содержит задание `node`, поэтому при локальном запуске этот источник будет недоступен. Источник Prometheus и дашборд в Grafana настраиваются отдельно; локальный Compose не подключает provisioning правил.

```bash
# Логи приложения
docker compose logs -f app

# Остановка с сохранением томов
docker compose down
```

## API

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/` | Информация о версии и времени выполнения обработчика |
| GET | `/health` | Ответ `{"status":"ok"}` |
| GET | `/posts?limit=10` | Последние посты, новые сверху; limit от 1 до 100 |
| POST | `/posts` | Создание поста, ответ HTTP 201 |
| GET | `/metrics` | Метрики в формате Prometheus |

```bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/posts \
  -H 'Content-Type: application/json' \
  -d '{"title":"Первый пост","content":"Приложение работает"}'

curl 'http://localhost:8000/posts?limit=5'
```

Реализованы создание и чтение постов. Обновление, удаление и авторизация пользователей пока отсутствуют. `/health` проверяет ответ приложения, отдельного запроса к БД в этом обработчике нет.

## Проверки кода

GitLab CI и GitHub Actions запускают:

```bash
ruff check .
ruff format --check .
pytest -v
```

Тесты проверяют health endpoint, создание поста, порядок выдачи, ограничение количества и валидацию полей. Для pytest нужна отдельная PostgreSQL-база с именем, заканчивающимся на `_test`: тестовая фикстура пересоздаёт таблицы.

Для запуска проверок на Mac при работающем локальном контейнере PostgreSQL:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# Выполнить один раз, если тестовой базы ещё нет.
docker compose exec db createdb -U app_user app_test

export TEST_DATABASE_URL='postgresql://app_user:app_pass@localhost:5433/app_test'
ruff check .
ruff format --check .
pytest -v
```

## CI/CD и серверное развёртывание

Основной pipeline описан в `.gitlab-ci.yml`:

1. **lint** — проверка кода и форматирования Ruff.
2. **test** — pytest с PostgreSQL service и базой `app_test`.
3. **build** — сборка Docker-образа и публикация в GitLab Registry с тегом `$CI_COMMIT_SHA`.
4. **deploy** — для `main`: доставка Compose и конфигураций мониторинга по SSH, обновление `IMAGE_TAG`, скачивание `app` и `node-exporter` с тремя попытками, `docker compose up -d --wait`.
5. **publish-docs** — для `main`: публикация HTML-страниц через GitLab Pages.

Дополнительный workflow `.github/workflows/ci.yml` проверяет код, запускает тесты и публикует образ в GHCR. Серверный Compose использует GitLab Registry.

### Предварительная настройка ВМ

Деплой рассчитан на пользователя `goha46` и каталог `/home/goha46`. На новой ВМ нужно отдельно подготовить Docker Compose, доступ SSH, необходимые права для команд `sudo -n`, каталог `init` с SQL и каталоги мониторинга. Скрипты бэкапа и unit-файлы systemd пока устанавливаются вручную.

GitLab CI/CD variables:

| Переменная | Назначение |
|---|---|
| `DEPLOY_HOST` | Актуальный адрес ВМ |
| `SSH_PRIVATE_KEY` | File variable с приватным ключом деплоя |
| `SSH_KNOWN_HOSTS` | File variable с проверенным ключом сервера для алиаса `devops-pet-vm` |

В `/home/goha46/.env` на сервере задаются:

```dotenv
IMAGE_TAG=<git-commit-sha>
DB_PASSWORD=<database-password>
GMAIL_ADDRESS=<sender@gmail.com>
GMAIL_APP_PASSWORD=<gmail-app-password>
```

Для пароля БД в составе `DATABASE_URL` нужно учитывать URL-кодирование специальных символов. `.env`, SSH-ключи, OAuth-токены и конфигурация rclone не должны попадать в Git.

```bash
# На сервере, из /home/goha46
docker compose -f compose.deploy.yml ps
docker compose -f compose.deploy.yml logs --tail=50 app
```

После изменения смонтированных конфигураций работающие процессы должны перечитать их. В текущем процессе это выполняется вручную:

```bash
sudo docker compose -f compose.deploy.yml restart prometheus
sudo docker compose -f compose.deploy.yml restart grafana
```

## Мониторинг и оповещения

Prometheus опрашивает приложение и Node Exporter каждые 15 секунд. На настроенной ВМ Grafana показывает запросы в секунду и доступность API.

| Правило | Условие | Интервал / ожидание |
|---|---|---|
| API недоступен | `up{job="fastapi"} < 1` | 1 минута / 1 минута |
| Резервная копия устарела | Возраст успешного бэкапа больше 93600 секунд | 5 минут / 5 минут |

Возраст бэкапа вычисляется так:

```promql
time() - postgres_backup_last_success_timestamp_seconds{job="node"}
```

Для правила бэкапов отсутствие данных и ошибка запроса также переводят правило в Alerting. Правила хранятся в `monitoring/grafana/alerting/` и загружаются Grafana при запуске.

YAML содержит UID источника Prometheus и имя contact point `Egor Ilin` текущего экземпляра Grafana. При переносе на новый экземпляр нужно создать источник и почтовый контакт, затем согласовать UID и имя получателя. Дашборд, источник данных и contact point пока не разворачиваются автоматически из репозитория.

Доступ к серверной Grafana с Mac:

```bash
ssh -N -L 127.0.0.1:3001:127.0.0.1:3000 goha46@<vm-ip>
```

После подключения открыть http://localhost:3001. Внешний порт Grafana открывать не требуется.

## Резервное копирование

Скрипт `scripts/backup-postgres.sh` выполняет:

1. Создание архива `pg_dump -Fc` из контейнера `postgres_db`.
2. Проверку непустого файла и чтение оглавления через `pg_restore --list`.
3. Загрузку через remote `backup_crypt:` с шифрованием содержимого и названий файлов.
4. Удаление облачных копий старше 30 дней и локальных старше 7 дней.
5. Атомарную запись времени успешного завершения в `~/monitoring/textfile/postgres_backup.prom`.

`pg_restore --list` проверяет читаемость оглавления и не заменяет пробное восстановление. Если одна из команд завершается с ошибкой, время последнего успеха не обновляется.

### Настройка и запуск

На сервере нужны rclone с авторизованным remote `gdrive:`, remote `backup_crypt:` типа crypt поверх `gdrive:TestDocker-backups` и сохранённый вне ВМ пароль шифрования. OAuth-приложение Google настроено в статусе In production. Файл `~/.config/rclone/rclone.conf` содержит секреты и хранится с правами `600`.

Текущий сервис запускается от `goha46`. Для Docker-команд из скрипта необходим настроенный доступ `sudo -n` без интерактивного ввода пароля.

```bash
# Установка из клонированного репозитория на ВМ
mkdir -p ~/scripts ~/backups ~/monitoring/textfile
chmod 700 ~/backups
chmod 755 ~/monitoring/textfile
install -m 700 scripts/backup-postgres.sh ~/scripts/backup-postgres.sh
sudo install -m 644 systemd/backup-postgres.service /etc/systemd/system/
sudo install -m 644 systemd/backup-postgres.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now backup-postgres.timer

# Ручной запуск и диагностика
sudo systemctl start backup-postgres.service
sudo journalctl -u backup-postgres.service -n 50 --no-pager
systemctl list-timers backup-postgres.timer
rclone lsf backup_crypt:
```

Таймер настроен на **03:00 Europe/Moscow ежедневно**. `Persistent=true` позволяет выполнить пропущенный запуск после включения ВМ. Имена архивов содержат дату и время в UTC.

### Проверка восстановления в отдельную базу

Выбрать существующий архив и скачать его через crypt remote: rclone расшифрует содержимое автоматически.

```bash
mkdir -p ~/restore-check
chmod 700 ~/restore-check
# Указать имя существующего архива из rclone lsf backup_crypt:
BACKUP_NAME='app_db_20261025_114943.dump'
rclone copy "backup_crypt:$BACKUP_NAME" ~/restore-check/
chmod 600 ~/restore-check/*.dump

# Создать новую пустую базу для проверки.
sudo docker exec postgres_db sh -c \
  'PGPASSWORD="$POSTGRES_PASSWORD" createdb -U "$POSTGRES_USER" app_db_restore_check'

sudo docker exec -i postgres_db sh -c \
  'PGPASSWORD="$POSTGRES_PASSWORD" pg_restore -U "$POSTGRES_USER" -d app_db_restore_check --exit-on-error' \
  < "$HOME/restore-check/$BACKUP_NAME"

sudo docker exec postgres_db sh -c \
  'PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d app_db_restore_check -c "SELECT id, title, content FROM posts ORDER BY id;"'
```

В `BACKUP_NAME` указать имя нужного архива. Если проверочная база уже существует, использовать новое имя базы во всех командах. Для сравнения исходного и скачанного архивов можно выполнить `sha256sum` на сервере или `shasum -a 256` на Mac.

### Что проверено на практике

- Создание дампа и восстановление в отдельную PostgreSQL-базу с чтением постов.
- Совпадение SHA-256 архива после переноса на Mac.
- Загрузка через rclone crypt, скачивание и совпадение SHA-256 после расшифровки.
- Ручной запуск бэкапа через systemd и получение метрики Prometheus.
- Срабатывание правила свежести с временным порогом и доставка письма; рабочий порог возвращён на 26 часов.
- Загрузка правила из YAML: статус Provisioned / Normal.

Автоматический ночной запуск по расписанию пока отдельно не подтверждён. Подтверждён ручной запуск того же systemd-сервиса.

## Текущие ограничения и дальнейший план

- [ ] Подключить Nginx, домен и HTTPS; ограничить прямой внешний доступ к FastAPI.
- [ ] Реализовать и проверить откат на предыдущий образ.
- [ ] Подтвердить запуск бэкапа по расписанию и периодически проверять восстановление.
- [ ] Автоматизировать установку бэкапов, systemd и подготовку ВМ через Ansible.
- [ ] Описать облачную инфраструктуру через Terraform.
- [ ] Добавить provisioning источника данных, дашборда и почтового контакта Grafana.
- [ ] Разделить локальные и серверные настройки мониторинга.

Мониторинг расположен на той же ВМ: при полной недоступности машины её Grafana не сможет отправить письмо. Для такого случая нужен внешний мониторинг. Приложение пока доступно по HTTP без авторизации; оно предназначено для учебных данных.

## Страницы приложения резервного копирования

[Описание приложения](https://devops-pet-project-4a17fa.gitlab.io/) · [Политика конфиденциальности](https://devops-pet-project-4a17fa.gitlab.io/privacy.html)

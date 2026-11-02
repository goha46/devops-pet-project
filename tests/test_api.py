"""Тесты API: создание, список, лимит и валидация постов."""

import pytest


def test_health(client):
    """GET /health отвечает 200 и {"status": "ok"}."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_post(client):
    """POST /posts создаёт пост: статус 201, в ответе поля и
    служебные id/created_at."""
    response = client.post("/posts", json={"title": "Test", "content": "Testing..."})
    assert response.status_code == 201

    data = response.json()
    assert data["title"] == "Test"
    assert data["content"] == "Testing..."
    assert "id" in data
    assert "created_at" in data


def test_list_posts_newest_first(client):
    """GET /posts возвращает все посты, новые сверху."""
    first_post = {"title": "First test", "content": "First testing..."}
    second_post = {"title": "Second test", "content": "Second testing..."}
    client.post("/posts", json=first_post)
    client.post("/posts", json=second_post)

    response = client.get("/posts")
    assert response.status_code == 200

    posts = response.json()
    assert len(posts) == 2
    assert posts[0]["title"] == second_post["title"]
    assert posts[0]["content"] == second_post["content"]
    assert posts[1]["title"] == first_post["title"]
    assert posts[1]["content"] == first_post["content"]


def test_list_posts_limit(client):
    """GET /posts?limit=2 возвращает два самых новых поста из трёх."""
    for title in ["First", "Second", "Third"]:
        client.post("/posts", json={"title": title, "content": "Testing..."})

    response = client.get("/posts?limit=2")
    assert response.status_code == 200

    posts = response.json()
    assert len(posts) == 2
    assert [p["title"] for p in posts] == ["Third", "Second"]


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"title": "", "content": "text"}, id="empty_title"),
        pytest.param({"title": "x", "content": ""}, id="empty_content"),
        pytest.param({"title": "", "content": ""}, id="both_empty"),
        pytest.param({"content": "text"}, id="missing_title"),
        pytest.param({"title": "x"}, id="missing_content"),
        pytest.param({"title": "a" * 256, "content": "x"}, id="title_too_long"),
    ],
)
def test_create_post_validation(client, payload):
    """POST /posts с невалидными данными отвечает 422
    (правила из схемы PostCreate)."""
    response = client.post("/posts", json=payload)
    assert response.status_code == 422
